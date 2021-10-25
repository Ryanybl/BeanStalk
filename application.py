from flask import Flask, Response
import RDBService as db
import json
application = Flask(__name__)

@application.route("/")
def index():
    return "Your Flask App Works!"

@application.route("/hello")
def hello():
    return "Hello World!"

@application.route('/catalog')
def get_catalog():
    res = db.RDBService.get_all("products", "products")
    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp

if __name__ == "__main__":
    application.run(port=5000, debug=True)