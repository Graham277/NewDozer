import logging
import json
import socket
import sqlite3
import sys
import threading
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

class Status(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
class AttendanceCodeCommunicator:

    db_connection = None
    db_temp = {}
    status: Status = Status.DISCONNECTED
    thread: threading.Thread = None

    def __init__(self, db_path):
        db_connection = sqlite3.connect(db_path)
        db_connection.execute("CREATE TABLE IF NOT EXISTS Attendance ( user VARCHAR(255), timestamp INTEGER );")

    def _discover(self, sock: socket.socket):

        const_version = 1
        logging.log(logging.DEBUG, "Discovering available endpoints")

        while True:
            try:
                message = json.loads(sock.recv(1024))
            except ValueError:
                continue
            if message['app'] == 'attendance' and message['type'] == 'discovery' and message['version'] == const_version:
                logging.log(logging.DEBUG, "Found an available endpoint")
                return message['host']

    def _handshake(self, sock: socket.socket):

        connect_message = json.loads(sock.recv(1024))
        if connect_message['type'] != 'connect':
            logging.log(logging.ERROR, f"Failed to connect with endpoint, wrong type {connect_message['type']}")
            return False # let endpoint try again

        response = {
            'type': 'acknowledge',
            'targeting': connect_message['type']
        }
        val1_tmp = json.dumps(response)
        val2_tmp = val1_tmp.encode()
        sock.send(val2_tmp)
        return True

    def _communicate_after_handshake(self, sock: socket.socket):

        const_code_show_duration = 30 # seconds
        const_code_valid_duration = 60 # seconds

        counter = 0

        while True:

            data = sock.recv(1024)
            if len(data) == 0:
                logging.log(logging.WARN, "Remote endpoint disconnected")
                return

            message = json.loads(data)

            if message['type'] == 'heartbeat':
                counter += 1
                if counter != message['counter']:
                    response = {
                        'type': 'heartbeat_error',
                        'counter': counter
                    }
                    sock.sendall(bytes(json.dumps(response), 'utf-8'))

                    logging.log(logging.WARN,
                                f"Connection error with attendance code endpoint: got counter {message['counter']}, expected {counter}")

                else:
                    response = {
                        'type': 'acknowledge',
                        'targeting': message['type'],
                        'counter': counter
                    }
                    sock.sendall(bytes(json.dumps(response), 'utf-8'))

            elif message['type'] == 'code':
                code = int(message['code'])
                generation_time = int(message['generation_time'])
                response = {
                    'type': 'acknowledge',
                    'targeting': message['type'],
                    'code': code,
                    'valid_to': generation_time + const_code_show_duration
                }
                sock.sendall(bytes(json.dumps(response), 'utf-8'))
                self.db_temp[response['code']] = generation_time + const_code_valid_duration

            else:
                logging.log(logging.WARN, f"Unknown message {message['type']}, ignoring")

    def _communicate(self):
        """
        Attempt to communicate with the remote screen.
        Handles both broadcasts and regular communication.
        Intended to be run as a thread
        :return:  None
        """
        while True:
            logging.log(logging.INFO, f"Communicator thread started")
            broadcast_in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_in_sock.bind(('0.0.0.0', 5789))
            logging.log(logging.INFO, "Now listening on 0.0.0.0 port 5789")
            host = self._discover(broadcast_in_sock)
            logging.log(logging.INFO, "Found an endpoint")
            self.status = Status.CONNECTING
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, 5789))

            if self._handshake(sock):
                self.status = Status.CONNECTED
                self._communicate_after_handshake(sock)


    def run(self):
        # Specs:
        #
        # A screen sends out a 255.255.255.255 broadcast app: attendance, type: discovery, version: 1 (as of now), host matching local IP
        # Server connects to host given in the parameter
        #
        # On connect, screen sends JSON object with type = "connect"
        # Server sends type = "acknowledge", targeting = "connect"
        # On every code generation event (screen): type = "code", code = <generated code>, generation_time = <generation Unix timestamp>
        # Server acknowledges with type = "acknowledge", targeting = "code", code = <same>, valid_to = <expiry time>
        # Every 10s, screen sends type = "heartbeat", counter = <counter that increments each heartbeat>
        # Server sends type = "acknowledge", targeting = "heartbeat", counter = <counter>
        #
        # Errors:
        # If the heartbeat counters do not match, server sends type = "heartbeat_error", counter = <corrected value>
        # If connection fails, disconnect and try again after 10s
        #
        # Note that the "server" here is the discord bot, but the server is technically the tablet

        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
        logging.log(logging.INFO, f"Starting attendance communicator")
        self.thread = threading.Thread(target=self._communicate, daemon=True)
        self.thread.start()
