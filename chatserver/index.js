'use strict';

// libraries and imports
const uuidv4 = require('uuid/v4');
const path = require('path');
const express = require('express');
const app = express();
const http = require('http').Server(app);
const bodyParser = require('body-parser');
const io = require('socket.io')(http);
const port = process.env.PORT || 3000;

// application-specific variables
const state = {};
const sockets = {};

// AWS config
const AWS = require('aws-sdk');
AWS.config.update({
  region: 'us-east-1',
  credentials: new AWS.CognitoIdentityCredentials({
      // IdentityPoolId: 'us-east-1:0644c03b-dc36-4e91-ae48-b2a2d71ffa3c',
      IdentityPoolId: 'us-east-1:6b8882b9-33c1-4885-aeb1-bf836cddb79f',
  })
});
const s3 = new AWS.S3({
  params: { Bucket: 'ai-customer-group6-conversations' },
  accessKeyId: 'AKIAJOJQFSEGYR5TA6QQ',
  secretAccessKey: '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'
});
const lexruntime = new AWS.LexRuntime();

// helper function for initializing state
const initState = function(userId) {
  return {
    userId,
    name: '',
    messages: [],
    sessionAttributes: {},
    conversationId: uuidv4() // auto-assign conversationId
  };
};

// helper function for pushing user message to lex
function pushMsg(userId, inputText) {
  let msg = {
    inputText,
    userId,
    sessionAttributes: state[userId].sessionAttributes,
    botAlias: '$LATEST',
    botName: 'BookTrip',
  };
  lexruntime.postText(msg, function(err, data) {
    if (err) {
      console.log(err);
      return 'Error';
    } else if (data) {
      console.log(data);
      state[userId].sessionAttributes = data.sessionAttributes;
      state[userId].messages.push(data.message);
      io.emit(userId, textMessage(data.message));
      if (data.dialogState === 'Fulfilled') {
        console.log('Saving to S3...');
        s3.upload({
          Key: `${userId}.json`,
          ContentType: 'application/json',
          Body: JSON.stringify(state[userId]),
          UploadId: userId,
          ACL: 'public-read'
        },function (resp) {
          console.log(resp? 'Error' : 'Successfully uploaded messages to S3.');
        });
      }
    }
  });
}

// wraps a string as a text message
// ready to be sent through socket.io
const textMessage = function(text) {
  if (typeof text !== 'string') {
    throw new Error('text parameter needs to be a string');
  }

  return JSON.stringify({
    text: text
  });
};

io.on('connection', function(socket) {

  console.log(`socket ${socket.id} connected ${new Date().toISOString()}`);

  sockets[socket.id] = socket;
  let socketRef = socket;

  socket.on('handshake', function(userObj) {
    console.log(`received handshake for user`, userObj);

    try {
      let user = JSON.parse(userObj);
      let userId = user.userId || user.agentId;

      // if a state object does not exist
      // for this user, create a new one
      if (!state[userId]) {
        console.log(userId + ' logged in!');
        state[userId] = initState(userId);
        state[userId].name = user.name;
      }

      // event handler for messages from this particular user
      socketRef.on(userId, function(message) {
        console.log(`received message for ${userId}`, message);

        let currentState = state[userId];

        // track the message
        currentState.messages.push(message);

        // TODO: below, you need to handle the incoming message
        // and use Lex to disambiguate the user utterances
        // io.emit(userId, textMessage(`Hi there. I'm under development, but should be functional soon :)`));
        pushMsg(userId, message);
      });
    } catch (handshakeError) {
      console.log('user handshake error', handshakeError);
    }
  });

  socket.on('agentHandshake', function(userObj) {
    console.log(`received handshake for agent`, userObj);

    try {
      let user = JSON.parse(userObj);
      // let userId = user.userId;
      let userId = user.agentId;

      // if a state object does not exist
      // for this user, create a new one
      if (!state[userId]) {
        state[userId] = initState(userId);
        state[userId].name = user.name;
      }

      // event handler for messages from this particular user
      socketRef.on(userId, function(message) {
        console.log(`received message for ${userId}`, message);

        let currentState = state[userId];

        // track the message
        currentState.messages.push(message);

        // TODO: below, you need to handle the incoming message
        // and use Lex to disambiguate the user utterances
        // io.emit(userId, textMessage(`Hi there. I'm under development, but should be functional soon :)`));
        pushMsg(userId, message);
      });
    } catch (handshakeError) {
      console.log('user handshake error', handshakeError);
    }
  });

  socket.on('disconnect', function() {
    console.log(`socket ${socket.id} disconnected at ${new Date().toISOString()}`);
    if (sockets[socket.id]) delete sockets[socket.id];
  });
});

// middleware
app.use(bodyParser.urlencoded());
app.use(bodyParser.json());
app.use('/assets', express.static(path.join(__dirname, 'assets')));

http.listen(port, function() {
  console.log('listening on *:' + port);
});

// serve up agent dashboard
app.get('/', function(req, res) {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// sent sentiment analysis
app.post('/sentiment', function(req, res) {
  res.send('Gotcha!');
  console.log('User sentiment received:');
  console.log(req.body);
  io.emit(req.body.uid, textMessage(`${req.body.label}(${req.body.score})`));
});
