webui
=====

a simple library for connecting html/js interfaces with a python server through websockets


### Example

An example app is included in the `example/` folder.  It is a good starting point for making a new app.  It can be run by doing something like...

    mkdir webui_example
	cd webui_example
	git clone https://github.com/cdoolin/webui.git
	cp -r webui/example/* .
	python example.py

### Dependencies

- python 2.7 (because gevent)
- gevent
- gevent-websocket
- bottle
