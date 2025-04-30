# from api.views import api
from flask import Flask

from temperature_api.api.views import api

app = Flask(__name__)
# app.config.from_object("settings")

app.register_blueprint(api, url_prefix="/api")
