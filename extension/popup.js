let isTranscribing = false;
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const transcriptionDiv = document.getElementById('transcription');

startBtn.addEventListener('click', () => {
  isTranscribing = true;
  startBtn.disabled = true;
  stopBtn.disabled = false;
  transcriptionDiv.textContent = 'Starting transcription...';
  chrome.runtime.sendMessage({ type: 'START' });
});

stopBtn.addEventListener('click', () => {
  isTranscribing = false;
  startBtn.disabled = false;
  stopBtn.disabled = true;
  transcriptionDiv.textContent += '\nTranscription stopped.';
  chrome.runtime.sendMessage({ type: 'STOP' });
});

// Listen for transcription updates
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'TRANSCRIPTION') {
    transcriptionDiv.textContent = message.text;
  }
}); 