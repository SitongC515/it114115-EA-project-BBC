# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask, request
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
# Optional Flask-Admin integration (dev mode)
try:
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView
    _FLASK_ADMIN_AVAILABLE = True
except Exception:
    Admin = None
    ModelView = None
    _FLASK_ADMIN_AVAILABLE = False

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager()
login.login_view = "login"
login.init_app(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)


from app import models

from flask_login import UserMixin  


@login.user_loader
def load_user(id):
    return models.User.query.get(int(id))

if not app.debug:
    root = logging.getLogger()
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        root.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.setLevel(logging.INFO)
    root.info('Microblog startup')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])


with app.app_context():
    db.create_all()

    # If Flask-Admin is installed (dev mode), register a simple admin interface
    if _FLASK_ADMIN_AVAILABLE:
        try:
            admin = Admin(app, name='Site Admin', template_mode='bootstrap3')
            # register a few simple model views if models exist
            try:
                admin.add_view(ModelView(models.User, db.session))
            except Exception:
                # ignore if a model can't be registered
                pass
        except Exception:
            # swallow admin initialization errors so production mode is unaffected
            pass


# duplicate/old loader removed — the valid @login.user_loader is defined above

from app import routes, errors