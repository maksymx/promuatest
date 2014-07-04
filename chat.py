from gevent import monkey
from flask import Flask, Response, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin


monkey.patch_all()

application = Flask(__name__)
application.debug = True
application.config['PORT'] = 5000
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/chat.db'
db = SQLAlchemy(application)


@application.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')

@application.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        application.logger.error("Exception while handling socketio connection",
                                 exc_info=True)
    return Response()


class ChatNamespace(BaseNamespace, BroadcastMixin):
    def initialize(self):
        self.logger = application.logger
        self.log("Socketio session started")

    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def recv_connect(self):
        self.log("New connection")

    def recv_disconnect(self):
        self.log("Client disconnected")

    def on_join(self, email):
        self.log("%s joined chat" % email)
        self.session['email'] = email
        return True, email

    def on_message(self, message):
        self.log('got a message: %s' % message)
        self.broadcast_event_not_me("message",{
            "sender" : self.session["email"],
            "content" : message})
        return True, message

    def on_createroom(self, room):
        pass

    def on_exitroom(self, room):
        pass

    def on_searchroom(self, room):
        pass

    def on_searchinchat(self, ):
        pass


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(20), unique=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username