from flask import Flask, Response
import database_services.RDBService as db
from flask_cors import CORS
import json

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from application_services.imdb_artists_resource import IMDBArtistResource
from application_services.UsersResource.user_service import UserResource


app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return '<u>Hello World!</u>'

@app.route('/catalog')
def get_catalog():
    res = db.RDBService.get_all("products", "products")
    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
