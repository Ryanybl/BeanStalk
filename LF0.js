var aws = require('aws-sdk');
aws.config.update({region: 'us-east-1'});
var lex = new aws.LexRuntime({apiVersion: '2016-11-28'})

function uuidv4() {
  //source: https://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function postText(userId, text, sessionId = null) {
    return new Promise((resolve, reject) => {
        
        var params = {
            botAlias: 'latest',
            botName: 'TestBot',
            inputText: text,
            userId: userId,
            sessionAttributes: {}
        };

        
        lex.postText(params, (err, data) => {
            if (err){
                reject(err);
            } else {
                resolve(data);
            }
        });
    });
}

exports.handler = async (event) => {
    
    var userId;
    
    if (!event.hasOwnProperty('userId')){
        userId = uuidv4();
    }else {
        userId = event.userId;
    }
    
    if (!event.hasOwnProperty('messages')){
        return {
            statusCode: 400,
            error: "messages is empty"
        };
    }
    var resMessages = [];
    
    for (var message of event.messages) {
        if (message.type === 'unstructured') {
            const res = await postText(userId, message.unstructured.text);
            resMessages.push({
                type: "unstructured",
                unstructured: {
                    text: res.message
                },
                data: res
            });
        } else {
          console.log('not implemented');
        }
    }

    const response = {
        messages: resMessages
    };
    
    return response;
};
