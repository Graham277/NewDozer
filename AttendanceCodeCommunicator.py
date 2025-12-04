import logging
import json
import socket
import sqlite3
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

    def __init__(self, db_path):
        db_connection = sqlite3.connect(db_path)
        db_connection.execute("CREATE TABLE IF NOT EXISTS Attendance ( user VARCHAR(255), timestamp INTEGER );")

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
        def _communicate():
            """
            Attempt to communicate with the remote screen.
            Handles both broadcasts and regular communication.
            Intended to be run as a thread
            :return:  None
            """
            logging.log(logging.INFO, f"Starting attendance communicator")
            broadcast_in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_in_sock.connect(('0.0.0.0', 5789))
            logging.log(logging.INFO, "Now listening on 0.0.0.0 port 5789")
            host = self._discover(broadcast_in_sock)
            logging.log(logging.INFO, "Found an endpoint")
            self.status = Status.CONNECTING
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, 5789))

            if self._handshake(sock):
                self.status = Status.CONNECTED
                self._communicate_after_handshake(sock)

        thread = threading.Thread(target=_communicate, daemon=True)
        thread.start()

    def _discover(self, sock: socket.socket):

        const_version = 1

        while True:
            try:
                message = json.loads(sock.recv(1024))
            except ValueError:
                continue
            if message['app'] == 'attendance' and message['type'] == 'discovery' and message['version'] == const_version:
                return message['host']

    def _handshake(self, sock: socket.socket):

        connect_message = json.loads(sock.recv(1024))
        if connect_message['type'] != 'connect':
            logging.log(logging.ERROR, f"Failed to connect with endpoint, wrong type {connect_message['type']}")
            return False # let endpoint try again after 10s

        response = {
            'type': 'acknowledge',
            'targeting': connect_message['type']
        }
        sock.sendall(bytes(json.dumps(response), 'utf-8'))
        return True

    def _communicate_after_handshake(self, sock: socket.socket):

        const_code_show_duration = 30 # seconds
        const_code_valid_duration = 60 # seconds

        counter = 0

        while True:
            message = json.loads(sock.recv(1024))

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