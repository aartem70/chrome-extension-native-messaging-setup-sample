import json
import sys
import time
import random

def send_message(message):
    """Send message to Chrome extension"""
    # Chrome native messaging protocol requires sending message size first
    message_json = json.dumps(message)
    sys.stdout.buffer.write(len(message_json).to_bytes(4, byteorder='little'))
    sys.stdout.buffer.write(message_json.encode('utf-8'))
    sys.stdout.buffer.flush()

def read_message():
    """Read message from Chrome extension"""
    # Read message length (first 4 bytes)
    length_bytes = sys.stdin.buffer.read(4)
    if not length_bytes:
        return None
    
    message_length = int.from_bytes(length_bytes, byteorder='little')
    message_json = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message_json)

def mock_transcribe():
    """Generate mock transcription text"""
    phrases = [
        "Hello world",
        "This is a test",
        "Real-time transcription demo",
        "Native messaging works",
        "Python and Chrome working together"
    ]
    return random.choice(phrases)

def main():
    try:
        while True:
            # Read message from extension
            message = read_message()
            if message is None:
                break

            if message.get('type') == 'START':
                # Simulate real-time transcription
                while True:
                    transcription = mock_transcribe()
                    send_message({
                        'type': 'TRANSCRIPTION',
                        'text': transcription,
                        'timestamp': time.time()
                    })
                    time.sleep(2)  # Simulate delay between transcriptions
            
            elif message.get('type') == 'STOP':
                send_message({
                    'type': 'STOPPED',
                    'message': 'Transcription stopped'
                })
                break

    except Exception as e:
        send_message({
            'type': 'ERROR',
            'message': str(e)
        })
        sys.exit(1)

if __name__ == '__main__':
    main() 