// console.log wrapper
const isLog = true;
function LOG(...args) {
   if (isLog) console.log(...args);
}
// console.log color
const C_RED = '\x1B[31m';
const C_RST = '\x1B[0m';

const express = require('express');
const bodyParser = require('body-parser');

const cors = require('cors');
require('dotenv').config({ debug: isLog });


const AssistantV2 = require('ibm-watson/assistant/v2');
const { IamAuthenticator } =require('ibm-watson/auth');
const WA_VARSION = '2023-06-15';

var server = express();
server
   .use(bodyParser.json())
   .use(bodyParser.urlencoded({
     extended: false
   }))
   .use(express.static('public'))

   // CORS
   .use(cors())

   .get('/', function (req, res) {
      res.send('watson assistant bridge!')
   })

   .post('/api', async (req, res) => {
      if (typeof process.env.API_KEY == 'undefined') {
         console.error('Error: "API_KEY" is not set.');
         console.error('Please consider adding a .env file with API_KEY.');
         return;
      }

      let body = req.body;
      // Check Params
      if (!(body.params)) {
         res.status(500).send({"error": "Invalid projectId!"});
         return;
      }

      const assistant = new AssistantV2({
         authenticator: new IamAuthenticator({
            apikey: process.env.API_KEY,
         }),
         version: WA_VARSION,
         serviceUrl: process.env.API_BASE_URL,
      });

      switch (body.api) {
         case "messageStateless":
            assistant.messageStateless(body.params)
               .then(response => {
                  LOG(`${C_RED}${body.api}${C_RST}\n`, JSON.stringify(response.result, null, 2));
                  res.json(response.result);
               })
               .catch(err => {
                  LOG('error:', err);
                  res.status(500).send({"error": "Failed Watson Discovery query."});
               });
            break;

         default:
            LOG(`${C_RED}${body.api}${C_RST}\n`, "Unsupported api!");
            res.status(500).send({"error": "Unsupported api!"});
            break;
      }
   })

const port = process.env.PORT || 8080;
server.listen(port, () => {
  // eslint-disable-next-line no-console
  LOG(`Watson Assistant Server running on port: ${C_RED}${port}${C_RST}`);
});

