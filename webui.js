function _WebUI(){
    this.actions = {}

    var uri = 'ws://' + window.location.host + '/socket';
    this.ws = new WebSocket(uri);

    this.ws.onopen = function() {
        console.log('socket opened');
    };

    this.ws.onclose = function() {
        console.log("socket closed");
        if(this.onclose != undefined)
            this.onclose();
    }.bind(this);

    this.ws.onmessage = function(m) {
        m = JSON.parse(m.data);
        if(this.actions[m.action] != undefined)
            this.actions[m.action](m);
        else console.log("don't know how to " + m.action);
    }.bind(this);

};

_WebUI.prototype.call = function(action, args) {
    if(args == undefined)
        args = {}

    args["action"] = String(action);
    this.ws.send(JSON.stringify(args));
};


$(function(){
	webui = new _WebUI();
});


$.ajaxSetup ({
    // Disable caching of AJAX responses
    'cache': false,
});
