from chat import application, init_db
from gevent import monkey
from socketio.server import SocketIOServer


monkey.patch_all()
init_db()

if __name__ == '__main__':
    SocketIOServer(
        ('', application.config['PORT']), 
        application,
        resource="socket.io").serve_forever()