import logging
import json
import socketserver
from dotenv import load_dotenv

load_dotenv()

class AttendanceRequestHandler(socketserver.BaseRequestHandler):

    CONST_CODE_VALID_DURATION = 30 # seconds

    counter = 0

    def handle(self):
        connect_message = json.loads(self.request.recv(256))
        if connect_message['type'] != 'connect':
            logging.log(logging.ERROR, f"Failed to connect with client, wrong type {connect_message['type']}")
            return # let client try again after 10s

        response = {
            'type': 'acknowledge',
            'targeting': connect_message['type']
        }
        self.request.sendall(json.dumps(response))

        while True:
            message = json.loads(self.request.recv(256))

            if message['type'] == 'heartbeat':
                self.counter += 1
                if self.counter != message['counter']:
                    response = {
                        'type': 'heartbeat_error',
                        'counter': self.counter
                    }
                    self.request.sendall(json.dumps(response))

                    logging.log(logging.WARN, f"Connection error with attendance code client: got counter {message['counter']}, expected {self.counter}")

                else:
                    response = {
                        'type': 'acknowledge',
                        'targeting': message['type'],
                        'counter': self.counter
                    }
                    self.request.sendall(json.dumps(response))

            elif message['type'] == 'code':
                code = int(message['code'])
                generation_time = int(message['generation_time'])
                response = {
                    'type': 'acknowledge',
                    'targeting': message['type'],
                    'code': code,
                    'valid_to': generation_time + self.CONST_CODE_VALID_DURATION
                }
                self.request.sendall(json.dumps(response))
                # TODO commit to a db somewhere

            else:
                logging.log(logging.WARN, f"Unknown message {message['type']}, ignoring")

def run():
    # Specs:
    # On connect, send JSON object with type = "connect"
    # Server sends type = "acknowledge", targeting = "connect"
    # On every code generation event, type = "code", code = <generated code>, generation_time = <generation Unix timestamp>
    # Server acknowledges with type = "acknowledge", targeting = "code", code = <same>, valid_to = <expiry time>
    # Every 10s, send type = "heartbeat", counter = <counter that increments each heartbeat>
    # Server sends type = "acknowledge", targeting = "heartbeat", counter = <counter>
    # Errors:
    # If the heartbeat counters do not match, server sends type = "heartbeat_error", counter = <corrected value>
    # If connection fails, disconnect and try again after 10s
    server = socketserver.TCPServer(('localhost', 5789), AttendanceRequestHandler)
    server.serve_forever()