(function($,window){

    var chatAPI = {
        connect : function(done) {
            this.socket = io.connect('/chat');
            this.socket.on('connect', done);
        },

        join : function(email, onJoin){
            this.socket.emit('join', email, onJoin);
        }

    };  

    var bindUI = function(){
        $(".join-chat").validate({
            submitHandler: function(form) {
                chatAPI.join($(form).find("[name='email']").val(), 
                    function(joined, name){
                        if(joined){
                            alert("You've joined PROM UA chat");
                        }
                    });
            }
        });
    };

    var ready = function(){
        bindUI();
        console.log("Welcome to PROM UA chat");
        chatAPI.connect(function(){});
    };



    $(function(){ ready(); });

}($,window));