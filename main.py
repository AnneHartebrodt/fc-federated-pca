from bottle import Bottle, static_file
import jinja2
import os


from app.api_ctrl import api_server
from app.api_web import web_server
os.chdir('app')
server = Bottle()

if __name__ == '__main__':
    print('Starting app', flush=True)
    server.mount('/api', api_server)
    server.mount('/web', web_server)
    server.run(host='localhost', port=5000, debug=True, reloader=True)
