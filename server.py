from typing import Optional
from pydantic import BaseModel

# Server
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# LOG
import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

# Scores
from sumeval.metrics.rouge import RougeCalculator

# env
import os
from dotenv import load_dotenv
load_dotenv()

# IBM
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
WA_VARSION = '2023-06-15'
api_key = os.getenv("API_KEY", None) 
api_url = os.getenv("API_BASE_URL", None)

authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version=WA_VARSION,
    authenticator=authenticator
)
assistant.set_service_url(api_url)


app = FastAPI(debug=True)

# Parameters
class Inputs(BaseModel):
    message_type: str = "text"
    text: str = ""

class WAParam(BaseModel):
    assistantId: str = ""
    input: Inputs
    ref: Optional[str] = None # use referense answer for Score.

class Params(BaseModel):
    api: str = "messageStateless"
    params: WAParam

def callWatsonAssistant(wa_prm):
    logger.info('[callWatsonAssistant]')
    response = assistant.message_stateless(
        assistant_id=wa_prm.assistantId,
        input={
            'message_type': wa_prm.input.message_type,
            'text': wa_prm.input.text
        }
    ).get_result()
    return response

def checkScore(ref, answer):
    logger.info(f"[checkScore]: { ref }")
    rouge = RougeCalculator(stopwords=True, lang="ja")
    rets = {
        'rouge_1': rouge.rouge_n(summary=answer, references=ref, n=1),
        'rouge_2': rouge.rouge_n(summary=answer, references=[ref], n=2),
        'rouge_l': rouge.rouge_l(summary=answer, references=[ref])
    }
    logger.info(f"rouge results: { rets }")
    return rets

# Path Routing
@app.post("/api")
def api(params: Params):
    logger.info(f"[api]: { params }")
    match params.api:
        case "messageStateless":
            ret = callWatsonAssistant(params.params)
            return ret
        case "messageStateless_Score":
            ret = callWatsonAssistant(params.params)
            if (params.params.ref != None):
                rouge_ret = checkScore(params.params.ref, ret['output']['generic'][0]['text'])
                ret["score"] = rouge_ret
            return ret
        case _:
            return

# mount HTML file for root path
app.mount("/", StaticFiles(directory="public",html=True), name="public")

# server init
def start():
    logger.info('[start]')
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
    # uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

# init from python script
logger.info(f'__name__ = {__name__}')
if __name__ == "__main__":
    start()

# init manual command
# uvicorn main:app --reload
# http://localhost:8000/docs