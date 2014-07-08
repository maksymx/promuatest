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

    function parseRSS(url, container) {
      $.ajax({
        url: document.location.protocol + '//ajax.googleapis.com/ajax/services/feed/load?v=1.0&num=10&callback=?&q=' + encodeURIComponent(url),
        dataType: 'json',
        success: function(data) {
          //console.log(data.responseData.feed);
          message('News from YCOMBINATOR', '');
          $.each(data.responseData.feed.entries, function(key, value){
            var thehtml = '<p><a href="'+value.link+'" target="_blank">'+value.title+'</a></p>';
            $(container).append(thehtml);
          });
        }
      });
    }

    window.setInterval(function(){
        parseRSS('https://news.ycombinator.com/rss', '#lines')
    }, 300000);

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

//        $('#find-message').submit(function () {
//            var text = $('#search').val();
//            socket.emit('get messages', text, function(msg){
//                //TODO: underline searched message
//                $("#lines").get(msg).scrollTop = 10000000;
//            });
//            return false;
//        });

        function clear () {
            $('#message').val('').focus();
        }
    });

});