#
# Simple WebUI example app
#
# includes:
#   example.py
#   static/index.html
#   static/example.js
#   static/extern/jquery-2.1.1.min.js
#

from webui import action, every, server, uis

@action
def click(word=""):
    print(word)
    uis.hello(txt="clicked")


@every(3)
def saysthings():
    uis.hello(txt="server ping")

serv = server(1234)
serv.serve_forever()
