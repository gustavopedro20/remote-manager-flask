from flask_cors import CORS
from flask import Flask, request, jsonify
from services import ssh
from models import Config

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/test', methods=['POST'])
def test():
    rqt = request.get_json()
    r = ssh.connect(rqt['ip'], rqt['port'], rqt['username'], rqt['password'])
    return jsonify(r)


if __name__ == "__main__":
    app.run(debug=True)
