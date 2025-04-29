from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt
from sqlalchemy import Column, Integer, String, DateTime
from flask_login import UserMixin
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash, check_password_hash


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

assoc_user_role = db.Table(
    'ab_user_role', db.Model.metadata,  # use db.Model.metadata
    db.Column('id', db.Integer, primary_key=True),  
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.UniqueConstraint('user_id', 'role_id')  
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', secondary=assoc_user_role, backref='roles', lazy='dynamic')

    def __repr__(self):
        return f"<Role(name='{self.name}')>"
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, followers.c.followed_id == Post.user_id
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({"reset_password": self.id,
                           "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)},
                          app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")[
                "reset_password"]
        except:           
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Post {self.body}>'
    
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f"Article('{self.title}', '{self.date_posted}')"
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='comments')

    def __repr__(self):
        return f"Comment('{self.text}', '{self.date_posted}')"
    
class WeatherData(db.Model):
    __tablename__ = "weather_data"  # Define the table name!

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(64), index=True)
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    today_temperature_high = db.Column(db.Integer)
    today_temperature_low = db.Column(db.Integer)
    today_description = db.Column(db.String(128))
    today_icon = db.Column(db.String(256))

    def __repr__(self):
        return f"WeatherData('{self.city}', '{self.date}', '{self.today_temperature_high}', '{self.today_temperature_low}', '{self.today_description}')"
    
class Menu(db.Model):
    __tablename__ = "menu"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(256))
    icon = db.Column(db.String(64))
    parent_id = db.Column(db.Integer, db.ForeignKey('menu.id'))
    order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    children = db.relationship('Menu', backref=db.backref('parent', remote_side=[id]))
    category = db.relationship('Category', backref='menu', lazy=True)
    
    def __repr__(self):
        return f"Menu('{self.name}')"

class Category(db.Model):
    __tablename__ = "category"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id')) 

    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    articles = db.relationship('Article', secondary='article_category',
                             backref=db.backref('categories', lazy='dynamic'),
                             lazy='dynamic')
    
    def __repr__(self):
        return f"Category('{self.name}')"

class ArticleCategory(db.Model):
    __tablename__ = "article_category"
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    article = db.relationship('Article', backref=db.backref('article_categories', lazy=True))
    category = db.relationship('Category', backref=db.backref('article_categories', lazy=True))
    
    def __repr__(self):
        return f"ArticleCategory(article_id={self.article_id}, category_id={self.category_id})"


class Permission(db.Model):
    __tablename__ = "permission"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    password = db.Column(db.String(30))


class ViewMenu(db.Model):
    __tablename__ = 'view_menu'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    

class PermissionView(db.Model):
    __tablename__ = 'permission_view'

    id = db.Column(db.Integer, primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'))
    permission = db.relationship("Permission")
    view_menu_id = db.Column(db.Integer, db.ForeignKey('view_menu.id'))
    view_menu = db.relationship("ViewMenu")