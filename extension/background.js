let port = null;

// Connect to native messaging host
function connectToHost() {
  port = chrome.runtime.connectNative("com.your.speechrecognition");
  
  port.onMessage.addListener((message) => {
    if (message.type === 'TRANSCRIPTION') {
      // Forward transcription to popup
      chrome.runtime.sendMessage(message);
    }
  });

  port.onDisconnect.addListener(() => {
    port = null;
  });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'START') {
    if (!port) connectToHost();
    port.postMessage({ type: 'START' });
  } 
  else if (message.type === 'STOP') {
    if (port) {
      port.postMessage({ type: 'STOP' });
      port.disconnect();
      port = null;
    }
  }
}); 