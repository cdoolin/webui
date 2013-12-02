#!/usr/bin/env python
from bottle import Bottle, static_file, view, request, abort

import os
ROOT = os.path.dirname(os.path.realpath(__file__))

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketHandler, WebSocketError

import json

from decorators import actions


def disconnected(func):
    """
    decorator to make a function called when all clients are
    disconnected from the webserver.
    """
    disconnected.funcs.append(func)
disconnected.funcs = []



class Handler(object):
    """
    class to handle websocket connections.  a new instance is
    created for every websocket connection.

    s is a class variable that holds a list of all open sockets.
    currents holds the websocket currently calling the actions
    so the ui variable points to the right socket.
    """
    s = []
    currents = []

    def __init__(self, ws):
        self.ws = ws
        Handler.s.append(ws)

    def handle(self):
        """
        main loop for a connected websocket. this function
        should always be running while a socket it connected.
        this function should clean up the socket when it finished
        (ie. remove it from Handler.s
        """
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


        # remove websocket from connected socket list
        Handler.s.remove(self.ws)
        # check if no more sockets remain and call
        # disconnect functions if so.
        if len(Handler.s) is 0:
            for f in disconnected.funcs:
                f()

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
            try:
                actions[action](**m)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
            Handler.currents.pop()

class Caller(object):
    """
    convenience class so ui.action methods are dynamically created
    to call actions defined in the clients.
    """
    def __init__(self, socks):
        self.socks = socks

    def __getattr__(self, name):
        def makecall(**kwargs):
            kwargs.update({'action': name})
            for s in self.socks:
                s.send(json.dumps(kwargs))

        return makecall

# uis and ui global variables
uis = Caller(Handler.s)
ui = Caller(Handler.currents)



app = Bottle()

# create a bottle webapp

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
