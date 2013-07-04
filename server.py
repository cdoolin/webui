#!/usr/bin/env python
from bottle import Bottle, static_file, view, request, abort

import os
ROOT = os.path.dirname(os.path.realpath(__file__))

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketHandler, WebSocketError

import json

from decorators import actions

class Handler(object):
    s = []
    currents = []

    def __init__(self, ws):
        self.ws = ws
        Handler.s.append(ws)

    def handle(self):
        if "connected" in actions:
            Handler.currents.append(self.ws)
            actions["connected"]()
            Handler.currents.pop()

        go = True
        while go:
            try:
                m = self.ws.receive()
            except:
                m = None

            if m is None:
                go = False
            else:
                self.do_message(m)


        Handler.s.remove(self.ws)

    def do_message(self, m):
        try:
            m = json.loads(m)
        except ValueError:
            print("expected json from web")
            m = {}

        action = m.pop("action", None)

        if action is None:
            print("expected an action in ws")
        elif action not in actions:
            print("dont know how to %s" % action)
        else:
            Handler.currents.append(self.ws)
            actions[action](**m)
            Handler.currents.pop()

class Caller(object):
    def __init__(self, socks):
        self.socks = socks

    def __getattr__(self, name):
        def makecall(**kwargs):
            kwargs.update({'action': name})
            for s in self.socks:
                s.send(json.dumps(kwargs))

        return makecall

uis = Caller(Handler.s)
ui = Caller(Handler.currents)



app = Bottle()

@app.route("/")
def index():
    return static_file("index.html", 'static')

@app.route("/socket")
def handle_socket():
    ws = request.environ.get('wsgi.websocket')

    if not ws:
        print("bad websocket, aborting.")
        abort(400, "Expected WebSocket request.")

    h = Handler(ws)
    h.handle()


@app.route("/webui.js")
def index():
    return static_file("webui.js", ROOT)

@app.route("/<what:path>")
def static(what):
    return static_file(what, 'static')


def server(port):
    return WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)
