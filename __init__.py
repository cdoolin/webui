from gevent import monkey, sleep
monkey.patch_all()

from decorators import gthread, every, action

from server import server, ui, uis
