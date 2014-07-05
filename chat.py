from datetime import datetime

from gevent import monkey
from flask import Flask, Response, session, request, flash, url_for, redirect, render_template, abort ,g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user , logout_user , current_user , login_required
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

################## INITIALIZATION #####################
monkey.patch_all()

application = Flask(__name__)
application.debug = True
application.secret_key = 'why would I tell you my secret key?'
application.config['PORT'] = 5000
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'

db = SQLAlchemy(application)
login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = 'login'


##################### VIEWS ###########################
@application.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')

##### LOGIN & REGISTRATION #####


##### SOCKET PART #######
@application.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        application.logger.error("Exception while handling socketio connection",
                                 exc_info=True)
    return Response()


#################### NAMESPACE #########################
class ChatNamespace(BaseNamespace, BroadcastMixin):
    def initialize(self):
        self.logger = application.logger
        try:
            db.create_all()
        except:
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

    def on_register(self, username, email, passwd):
        try:
            user = User(username=username,
                        password=passwd,
                        email=email)
            db.session.add(user)
            db.session.commit()
            return True, username
        except:
            return False, username

    def on_login(self, username, passwd):
        registered_user = User.query.filter_by(username=username,password=passwd).first()
        if registered_user is None:
            return False
        self.log("User %s logged in successfully" % username)
        self.session['user'] = username
        return True, username

    def on_createroom(self, room):
        pass

    def on_exitroom(self, room):
        pass

    def on_searchroom(self, room):
        pass

    def on_searchinchat(self, ):
        pass


###################### ORM models ##################################
class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id',db.Integer , primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(10))
    email = db.Column('email',db.String(50),unique=True , index=True)
    registered_on = db.Column('registered_on' , db.DateTime)

    def __init__(self, username ,password , email):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.utcnow()

    def __repr__(self):
        return '<User %r>' % self.username


# class Room(db.Model):
#     __tablename__ = "rooms"
#     id = db.Column('user_id',db.Integer , primary_key=True)
#     roomname = db.Column('username', db.String(20), unique=True , index=True)
#     messages = db.relationship
#
#     def __init__(self):
#         pass
#
#
# class Message(db.Model):
#     __tablename__ = "messages"