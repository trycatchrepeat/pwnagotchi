import logging
import requests
import asyncio
from requests.auth import HTTPBasicAuth
from bettercap.websocket_client import WebSocketClient


class Client(object):
    def __init__(self, hostname='localhost', scheme='http', port=8081, username='user', password='pass'):
        self.hostname = hostname
        self.scheme = scheme
        self.port = port
        self.username = username
        self.password = password
        self.url = "%s://%s:%d/api" % (scheme, hostname, port)
        self.auth = HTTPBasicAuth(username, password)
        self.ws = WebSocketClient(scheme, hostname, port, username, password)

    def _decode(self, r, verbose_errors=True):
        try:
            return r.json()
        except Exception as e:
            if r.status_code == 200:
                logging.error("error while decoding json: error='%s' resp='%s'" % (e, r.text))
            else:
                err = "error %d: %s" % (r.status_code, r.text.strip())
                if verbose_errors:
                    logging.info(err)
                raise Exception(err)
            return r.text

    def session(self):
        r = requests.get("%s/session" % self.url, auth=self.auth)
        return self._decode(r)

    def events(self):
        r = requests.get("%s/events" % self.url, auth=self.auth)
        return self._decode(r)

    def events_listener(self, handler):
        loop = asyncio.get_event_loop()

        connection = loop.run_until_complete(self.ws.connect())

        tasks = [
            asyncio.ensure_future(self.ws.heartbeat(connection)),
            asyncio.ensure_future(self.ws.receiveMessage(connection, handler)),
        ]

        loop.run_until_complete(asyncio.wait(tasks))

    def run(self, command, verbose_errors=True):
        r = requests.post("%s/session" % self.url, auth=self.auth, json={'cmd': command})
        return self._decode(r, verbose_errors=verbose_errors)
