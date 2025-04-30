# from api.views import api
from flask import Flask

from dashboard_app.app.views import dashboard

app = Flask(__name__)
# app.config.from_object("settings")

app.register_blueprint(dashboard, url_prefix="/dashboard")
