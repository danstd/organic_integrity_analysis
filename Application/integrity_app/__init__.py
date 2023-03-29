from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv

USERNAME = getenv("FLASKUSER")
PSWD = getenv("FLASKUSER_DB_PSWD")
#HOST = "db"
HOST = getenv("HOST")
DB = getenv("DATABASE_NAME")

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{USERNAME}:{PSWD}@{HOST}/{DB}"

app = Flask("integrity_app")

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["HOST"] = "0.0.0.0"
#app.run(host=getenv("LOCAL_HOST"), port=5000)
#app.jinja_env.auto_reload = True
#app.config['TEMPLATES_AUTO_RELOAD'] = True
#app.run(host='0.0.0.0', debug=True)


db = SQLAlchemy(app)

import integrity_app.integrity_model
import integrity_app.integrity_routes

