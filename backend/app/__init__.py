import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app); migrate.init_app(app, db); jwt.init_app(app)
    origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})
    from . import models
    from .routes import api
    app.register_blueprint(api, url_prefix="/api")
    @app.get("/health")
    def health(): return jsonify(status="ok")
    return app
