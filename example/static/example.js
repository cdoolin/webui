// Example UI initialization

$(function(){
    console.log("loaded");
    
    // setup button click callback
    $('#butt').click(function() {
        console.log("clicked");
    
        // call action "click" on server with keyward argument word="hello".
        webui.call("click", {
            word: "hello",
        });
    });
    
    // setup client action callback that server calls
    webui.actions.hello = function(args) {
        console.log("got " + args.txt);
        var el = $('#thisp');
        el.css({opacity: "0.1"});
        el.text(args.txt);
        el.animate({opacity: "1."}, 200);
    };
});
