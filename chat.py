import re
import json
import unicodedata

from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from werkzeug.exceptions import NotFound
from gevent import monkey

from flask import Flask, Response, request, render_template, url_for, redirect, flash, make_response
from flask import session as flask_session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user, logout_user, login_required

monkey.patch_all()

application = Flask(__name__)
application.debug = True
application.secret_key = 'why would I tell you my secret key?'
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
application.config['PORT'] = 5000
db = SQLAlchemy(application)

login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return ChatUser.query.get(int(id))


############################### models #################################
class ChatRoom(db.Model):
    __tablename__ = 'chatrooms'
    id = db.Column('room_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(20), nullable=False, index=True)
    slug = db.Column('slug', db.String(50))
    messages = db.relationship('ChatMessages', backref='chatroom', lazy='dynamic')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return url_for('room', slug=self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        db.session.add(self)
        db.session.commit()

class ChatMessages(db.Model):
    __tablename__ = 'chatmessages'
    id = db.Column('id', db.Integer, primary_key=True)
    user = db.Column('user', db.String(20), nullable=False, index=True)
    text = db.Column('text', db.Text(200), index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chatrooms.room_id'))

    def __init__(self, user, text, room):
        self.user = user
        self.text = text
        self.room_id = room

    def __repr__(self):
        return '<Message %r, %r, %r>' % (self.user, self.text, self.room_id)


class ChatUser(db.Model):
    __tablename__ = 'chatusers'
    id = db.Column('user_id', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column('name', db.String(20), nullable=False, unique=True, index=True)
    password = db.Column('password', db.String(10))
    email = db.Column('email', db.String(50), unique=True, index=True)
    # session = db.Column(db.String(20), nullable=False)
    # chatroom_id = db.Column(db.Integer, db.ForeignKey('chatrooms.id'))

    def __init__(self, name, password, email):
        self.name = name
        self.password = password
        self.email = email

    def __unicode__(self):
        return self.name

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.name


############################## utils ##################################
def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)


def get_object_or_404(klass, **query):
    instance = klass.query.filter_by(**query).first()
    if not instance:
        raise NotFound()
    return instance


def get_or_create(klass, **kwargs):
    try:
        return get_object_or_404(klass, **kwargs), False
    except NotFound:
        instance = klass(**kwargs)
        instance.save()
        return instance, True


def init_db():
    db.create_all(app=application)


############################# views #####################################
@application.route('/')
@login_required
def rooms():
    """
    Homepage - lists all rooms.
    """
    context = {"rooms": ChatRoom.query.all()}
    return render_template('rooms.html', **context)


@application.route('/<path:slug>')
@login_required
def room(slug):
    """
    Show a room.
    """
    room = get_object_or_404(ChatRoom, slug=slug)
    msg = {i.text: i.user for i in ChatMessages.query.filter_by(room_id=room.id)}

    context = {"room": room,
               "messages": msg}
    return render_template('room.html', **context)


@application.route('/create', methods=['POST'])
@login_required
def create():
    """
    Handles post from the "Add room" form on the homepage, and
    redirects to the new room.
    """
    name = request.form.get("name")
    if name:
        room, created = get_or_create(ChatRoom, name=name)
        return redirect(url_for('room', slug=room.slug))
    return redirect(url_for('rooms'))


@application.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    user = ChatUser(request.form['username'],
                    request.form['password'],
                    request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))


@application.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True

    registered_user = ChatUser.query.filter_by(name=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))

    login_user(registered_user, remember=remember_me)
    resp = make_response(redirect(url_for('rooms')))
    resp.set_cookie('nickname', username)
    resp.set_cookie('logged', 'True')
    return resp

@application.route('/logout')
def logout():
    logout_user()
    flask_session.pop('logged', None)
    flask_session.pop('nickname', None)
    return redirect(url_for('rooms'))


####################### NAMESPACES ##############################
class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    nicknames = []

    def initialize(self):
        self.logger = application.logger
        self.log("Socketio session started")

    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def on_join(self, room):
        self.room = room
        self.join(room)
        return True

    def on_nickname(self, nickname):
        self.log('Nickname: {0}'.format(nickname))
        self.nicknames.append(nickname)
        self.session['nickname'] = nickname
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.nicknames)
        return True, nickname

    def recv_disconnect(self):
        # Remove nickname from the list.
        self.log('Disconnected')
        nickname = self.session['nickname']
        self.nicknames.remove(nickname)
        self.broadcast_event('announcement', '%s has disconnected' % nickname)
        self.broadcast_event('nicknames', self.nicknames)
        self.disconnect(silent=True)
        return True

    def on_user_message(self, msg, nick):
        self.emit_to_room(self.room, 'msg_to_room',
            self.session['nickname'], msg)
        msg = ChatMessages(nick, msg, room=self.room)
        db.session.add(msg)
        db.session.commit()
        return True

    def on_get_messages(self, msg):
        messages = ChatMessages.query.filter_by(text=msg, room_id=self.room).first()
        if messages:
            return messages


@application.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        application.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()


if __name__ == '__main__':
    application.run()
