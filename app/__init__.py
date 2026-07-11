from flask import Flask
from .extensions import db, migrate, bcrypt, jwt, mail, limiter, cors
from .config import config_by_name
import os


def create_app(config_name: str = None) -> Flask:
    """Application factory."""
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    # Ensure instance folder
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints (web)
    from .blueprints.auth import auth_bp
    from .blueprints.posts import posts_bp
    from .blueprints.comments import comments_bp
    from .blueprints.users import users_bp
    from .blueprints.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(posts_bp, url_prefix="/posts")
    app.register_blueprint(comments_bp, url_prefix="/comments")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Register API blueprints
    from .blueprints.api.auth import api_auth_bp
    from .blueprints.api.posts import api_posts_bp
    from .blueprints.api.comments import api_comments_bp
    from .blueprints.api.users import api_users_bp
    from .blueprints.api.admin import api_admin_bp

    app.register_blueprint(api_auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(api_posts_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(api_comments_bp, url_prefix="/api/v1/comments")
    app.register_blueprint(api_users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(api_admin_bp, url_prefix="/api/v1/admin")

    # Main index route
    from .blueprints.main import main_bp
    app.register_blueprint(main_bp)

    # Error handlers
    from .utils.errors import register_error_handlers
    register_error_handlers(app)

    # JWT callbacks
    from .utils.jwt_callbacks import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from .models import User, Post, Comment, Tag, Category, Like, Follow, Bookmark
        return dict(db=db, User=User, Post=Post, Comment=Comment,
                    Tag=Tag, Category=Category, Like=Like, Follow=Follow,
                    Bookmark=Bookmark)

    return app
