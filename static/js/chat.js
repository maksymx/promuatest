$(function() {

    var WEB_SOCKET_SWF_LOCATION = '/static/js/socketio/WebSocketMain.swf',

    socket = io.connect('/chat');

    socket.on('connect', function () {
        $('#chat').addClass('connected');
    });

    socket.on('announcement', function (msg) {
        $('#lines').append($('<p>').append($('<em>').text(msg)));
    });

    socket.on('nicknames', function (nicknames) {
        $('#nicknames').empty().append($('<span>Online: </span>'));
        for (var i in nicknames) {
          $('#nicknames').append($('<b>').text(nicknames[i]));
        }
    });

    socket.on('msg_to_room', message);

    socket.on('reconnect', function () {
        $('#lines').remove();
        message('System', 'Reconnected to the server');
    });

    socket.on('reconnecting', function () {
        message('System', 'Attempting to re-connect to the server');
    });

    socket.on('error', function (e) {
        message('System', e ? e : 'A unknown error occurred');
    });

    function message(from, msg) {
        $('#lines').append($('<p>').append($('<b>').text(from), msg));
    }

    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i=0; i<ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1);
            if (c.indexOf(name) != -1) return c.substring(name.length,c.length);
        }
    return "";
    }

    // DOM manipulation
    $(function () {
            var nick = getCookie('nickname');
            var logged = getCookie('logged');
            socket.emit('nickname', nick, function (set) {
                if (set) {
                    clear();
                    return $('#chat').addClass('nickname-set');
                }
                $('#nickname-err').css('visibility', 'visible');
            });


        $('#send-message').submit(function () {
            var text = $('#message').val();
            message('Me', text);
            socket.emit('user message', text, nick);
            clear();
            $('#lines').get(0).scrollTop = 50000;
            return false;
        });

        $('#find-message').submit(function () {
            var text = $('#search').val();
            socket.emit('get messages', text, function(msg){
                //TODO: underline founded message
                $("#lines").get(msg).scrollTop = 10000000;
            });
            return false;
        });

        function clear () {
            $('#message').val('').focus();
        }
    });

});