import asyncio
import json
import logging
import websockets
from base64 import b64encode

class WebSocketClient():
    def __init__(self, scheme, hostname, port, username, password):
        ws_scheme = 'wss' if scheme == 'https' else 'ws'
        self.endpoint = "%s://%s:%d/api/events" % (ws_scheme, hostname, port)

        userAndPass = "%s:%s" % (username, password)
        self.auth = b64encode(userAndPass.encode()).decode("ascii")

        pass

    async def connect(self):
        try:
            self.connection = await websockets.client.connect(self.endpoint, extra_headers = {
                'Authorization': 'Basic ' + self.auth
            })

            if self.connection.open:
                logging.debug("Websocket connection succesful")
                await self.sendMessage('Hello!')
                return self.connection

        except websockets.exceptions.ConnectionClosed:
            logging.exception('Connection with server closed')

    async def sendMessage(self, message):
        await self.connection.send(message)

    async def receiveMessage(self, connection, handler):
        while True:
            try:
                message = await connection.recv()
                handler(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                logging.exception('Connection with server closed')
                break

    async def heartbeat(self, connection):
        while True:
            try:
                await connection.send('ping')
                await asyncio.sleep(5)
            except websockets.exceptions.ConnectionClosed:
                logging.exception('Connection with server closed')
                break 