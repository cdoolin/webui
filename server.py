#!/usr/bin/env python
from bottle import Bottle, static_file, view, request, abort

import os
ROOT = os.path.dirname(os.path.realpath(__file__))

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
from gevent.lock import RLock

import json

from decorators import actions

import logging
logger = logging.getLogger("webui")


def format_action(action, message):
    if logger.isEnabledFor(20): # if inabled for INFO
        argstr = ", ".join("%s=%s" % (k, v) for k, v in message.iteritems())
        return "%s(%s)" % (action, argstr)
    else:
        return action


def alldisconnected(func):
    """
    decorator to make a function called when all clients are
    disconnected from the webserver.
    """
    alldisconnected.funcs.append(func)
alldisconnected.funcs = []


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
        self.ws_addr = "%s:%s" % (
            self.ws.environ["REMOTE_ADDR"],
            self.ws.environ["REMOTE_PORT"])
        logger.info("%s connected" % self.ws_addr)

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

        if "disconnected" in actions:
            Handler.currents.append(self.ws)
            actions["disconnected"]()
            Handler.currents.pop()

        # remove websocket from connected socket list
        Handler.s.remove(self.ws)
        # check if no more sockets remain and call
        # disconnect functions if so.
        if len(Handler.s) is 0:
            for f in alldisconnected.funcs:
                f()
        logger.info("%s disconnected" % self.ws_addr)

    def do_message(self, m):
        try:
            m = json.loads(m)
        except ValueError:
            logger.warning("expected json from web")
            m = {}

        action = m.pop("action", None)
        logger.info("%s called %s" % (self.ws_addr, format_action(action, m)))

        if action is None:
            logger.warning("expected an action in ws message")
        elif action not in actions:
            logger.warning("dont know how to %s" % action)
        else:
            Handler.currents.append(self.ws)
            try:
                actions[action](**m)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error("while doing %s: %s" % (action, str(e)))
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
                if s.closed:
                    continue

                with s.environ['lock']:
                    try:
                        s.send(json.dumps(kwargs))
                    except WebSocketError as e:
                        logger.error("could not send message: %s" % str(e))

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
        logger.error("bad websocket, aborting.")
        abort(400, "bad request.")
    else:
        ws.environ['lock'] = RLock()
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
