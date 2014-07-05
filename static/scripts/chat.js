(function($,window){

    var chatAPI = {

        connect : function(done) {
            var that = this;

            this.socket = io.connect('/chat');
            this.socket.on('connect', done);
            this.socket.on('message', function(message){
                if(that.onMessage){
                    that.onMessage(message);
                }
            });
        },

        join : function(email, onJoin){
            this.socket.emit('join', email, onJoin);
        },

        login: function(username, password, onLogin){
            this.socket.emit('login', username, password, onLogin)
        },

        register: function(username, email, password, onRegister){
            this.socket.emit('register', username, email, password, onRegister)
        },

        create_room: function(room, onCreate){
            this.socket.emit('createroom', room, onCreate)
        },

        sendMessage : function(message, onSent) {
            this.socket.emit('message', message, onSent);
        }



    };  

    var bindUI = function(){
//        $(".join-chat").validate({
//            submitHandler: function(form) {
//                chatAPI.join($(form).find("[name='email']").val(),
//                    function(joined, name) {
//                        if(joined){
//                            alert("You've joined PROM UA CHAT");
//                            $(form).hide();
//                            $(".compose-message-form").show();
//                        }
//                    }
//                );
//            }
//        });

        $(".login").validate({
            submitHandler: function(form) {
                var username = $(form).find("[name='username']").val();
                var passwd = $(form).find("[name='pass']").val();
                chatAPI.login(username, passwd,
                    function(logged, username){
                        if(logged){
                            alert("User "+username+" logged in successfully");
                            $(form).hide();
                            $(".compose-message-form").show();
                            $(".create-room").show();
                        }else{
                            alert('Username or Password is invalid \n' +
                                'Please try to login again or register');
                            $(".register").show();
                        }
                    }
                );
            }
        });

        $(".register").validate({
            submitHandler: function(form) {
                var username = $(form).find("[name='username']").val();
                var passwd = $(form).find("[name='pass']").val();
                var email = $(form).find("[name='email']").val();
                chatAPI.register(username, email, passwd,
                    function(registered, username){
                        if(registered){
                            alert("User "+username+" successfully registered");
                            $(form).hide();
                            $(".login").show();
                        }else{
                            alert('Please try again later');
                        }
                    }
                );
            }
        });

        $(".compose-message-form").validate({
            submitHandler: function(form) {
                chatAPI.sendMessage($(form).find("[name='message']").val(),
                    function(sent,message){
                        if(sent){
                            $(".messages").append(
                                jQuery("<li>").html(
                                    "<b>Me</b>: " + message
                                )
                            ).show();
                        }
                    });
            }
        });

        $(".create-room").validate({
            submitHandler: function(form) {
                var roomname = $(form).find("[name='roomname']").val();
                chatAPI.create_room(roomname,
                    function(sent, room){
                        if(sent){
                            $(".rooms").append(
                                jQuery("<li>").html(
                                    "<b>"+room+"</b>"
                                )
                            ).show();
                        }
                    });
            }
        });

        chatAPI.onMessage = function(message){
            $(".messages").append(
                jQuery("<li>").html(
                    "<b>" + message.sender + "</b>: " + message.content
                )
            ).show();
        };
    };

    var ready = function(){
        bindUI();
        console.log("Welcome to PROM UA CHAT");
        chatAPI.connect(function(){});
    };



    $(function(){ ready(); });

}($,window));