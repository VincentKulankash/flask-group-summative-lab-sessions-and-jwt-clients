from flask import Flask, jsonify
from config import Config
from extensions import db, bcrypt, login_manager, migrate, cors
from models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    #CORS setup to allow the react frontend to send session cookies
    cors.init_app(
        app, 
        supports_credentials=True, 
        origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    @login_manager.user_loader
    def load_user(user_id):
        #Given a user id (stored in the session cookie) fetch teh user object
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error":"Unauthorized. Please log in."}), 401

    #Register blueprints to avoid circular imports errors
    from routes.auth import auth_bp
    from routes.diary_entries import diary_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(diary_bp)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Rollback the session in case of a database error
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    return app

