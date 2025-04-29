from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm,CommentForm
from app.models import User, Post, Comment, Article
from app.email import send_password_reset_email
from app.models import WeatherData
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from wtforms import TextAreaField, SubmitField

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())





@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('index.html.j2', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'explore', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'explore', page=posts.prev_num) if posts.prev_num else None
    return render_template('index.html.j2', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() 
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html.j2', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    print(f"Username: {username}")  # Check the username
    user = User.query.filter_by(username=username).first_or_404()
    print(f"User: {user}")  # Check if the user was found
    page = request.args.get('page', 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html.j2', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))

@app.route('/article', endpoint='Article')
@login_required
def article():
    # Here you would fetch actual world news articles or data.
    return render_template('Article.html.j2', title=_('Article'))

@app.route('/weather')
def weather():
    city_query = request.args.get('city')
    
    if city_query:
        # Search for specific city
        weather_data = WeatherData.query.filter(WeatherData.city.ilike(f'%{city_query}%')).all()
    else:
        # Get all weather data
        weather_data = WeatherData.query.all()
    
    return render_template('weather.html.j2', weather_data=weather_data)



@app.route('/init_db')  # Create a separate route for initialization
def init_db():
    with app.app_context():
        db.create_all()  # Create tables

        if not WeatherData.query.first():
            sample_weather = WeatherData(
                city="London",
                date=datetime.utcnow(),
                today_temperature_high=15,
                today_temperature_low=5,
                today_description="Cloudy",
                today_icon="https://png.pngtree.com/png-vector/20190214/ourmid/pngtree-vector-cloudy-icon-png-image_450295.jpg"
            )
            db.session.add(sample_weather)
            
            sample_weather2 = WeatherData(
                city="Chicago",
                date=datetime.utcnow(),
                today_temperature_high=20,
                today_temperature_low=10,
                today_description="Sunny",
                today_icon="https://cdn-icons-png.flaticon.com/128/697/697982.png"
            )
            db.session.add(sample_weather2)
            
            sample_weather3 = WeatherData(
                city="San Jose",
                date=datetime.utcnow(),
                today_temperature_high=28,
                today_temperature_low=20,
                today_description="Clear",
                today_icon="https://cdn-icons-png.flaticon.com/512/3222/3222807.png"
            )
            db.session.add(sample_weather3)
            
            sample_weather4 = WeatherData(
                city="Tbilisi",
                date=datetime.utcnow(),
                today_temperature_high=30,
                today_temperature_low=22,
                today_description="Sunny",
                today_icon="https://cdn-icons-png.flaticon.com/128/697/697982.png"
            )
            db.session.add(sample_weather4)
            
            sample_weather5 = WeatherData(
                city="Dakar",
                date=datetime.utcnow(),
                today_temperature_high=32,
                today_temperature_low=26,
                today_description="Hot",
                today_icon="https://cdn-icons-png.flaticon.com/512/8371/8371981.png"
            )
            db.session.add(sample_weather5)
            
            sample_weather6 = WeatherData(
                city="Mombasa",
                date=datetime.utcnow(),
                today_temperature_high=31,
                today_temperature_low=25,
                today_description="Humid",
                today_icon="https://e7.pngegg.com/pngimages/314/726/png-clipart-moisture-computer-icons-humidity-others-desktop-wallpaper-weather-icon-thumbnail.png"
            )
            db.session.add(sample_weather6)
            db.session.commit()
        return "Database initialized with sample data!"

@app.before_first_request
def create_tables():
    db.create_all()
    sample_weather = [
    {"city": "London", "high": 18, "low": 12, "description": "Partly Cloudy", "icon": "partly_cloudy"},
    {"city": "Chicago", "high": 25, "low": 18, "description": "Sunny", "icon": "sunny"},
    {"city": "San Jose", "high": 28, "low": 20, "description": "Clear", "icon": "clear"},
    {"city": "Tbilisi", "high": 30, "low": 22, "description": "Sunny", "icon": "sunny"},
    {"city": "Dakar", "high": 32, "low": 26, "description": "Hot", "icon": "hot"},
    {"city": "Mombasa", "high": 31, "low": 25, "description": "Humid", "icon": "humid"},
    {"city": "Brasilia", "high": 27, "low": 19, "description": "Partly Cloudy", "icon": "partly_cloudy"},
    {"city": "Cape Town", "high": 23, "low": 15, "description": "Windy", "icon": "windy"}
]


@app.route('/comment', methods=['GET', 'POST'])
@login_required
def comment():
    form = CommentForm()
    comments = Comment.query.order_by(Comment.date_posted.desc()).all()

    if form.validate_on_submit():
        text = form.comment.data
        try:
            new_comment = Comment(text=text, user_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
            flash('Your comment has been posted!', 'success')
            return redirect(url_for('comment'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while posting your comment. Please try again.', 'danger')
            return render_template('comment.html.j2', comments=comments, form=form, title='Comments')

    return render_template('comment.html.j2', comments=comments, form=form, title='Comments')

@app.route('/ArticleA')
@login_required
def ArticleA():
    return render_template('ArticleA.html.j2', title='ArticleA')

@app.route('/ArticleB')
@login_required
def ArticleB():
    return render_template('ArticleB.html.j2', title='ArticleB')

@app.route('/ArticleC')
@login_required
def ArticleC():
    return render_template('ArticleC.html.j2', title='ArticleC')

@app.route('/ArticleD')
@login_required
def ArticleD():
    return render_template('ArticleD.html.j2', title='ArticleD')

@app.route('/ArticleE')
@login_required
def ArticleE():
    return render_template('ArticleE.html.j2', title='ArticleE')

@app.route('/ArticleF')
@login_required
def ArticleF():
    return render_template('ArticleF.html.j2', title='ArticleF')

@app.errorhandler(404)
def page_not_found(e):  
    return render_template('404.html.j2', title='404'), 404

@app.route('/test_500')
def internal_server_error():
    return render_template('500.html.j2', title='500'), 500

@app.route('/setcookie', methods=['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        user = request.form['nm']  # Assuming 'nm' is the form field name
        resp = make_response(render_template('readcookie.html'))
        expire_date = datetime.datetime.now()
        expire_date = expire_date + datetime.timedelta(seconds=5)
        resp.set_cookie('userID', user, expires=expire_date)
        resp.set_cookie('secureUserID', user, expires=expire_date, secure=True)
        resp.set_cookie('httpOnlyUserID', user, expires=expire_date, httponly=True)
        return resp

@app.route('/getcookie')
def getcookie():
    userID = request.cookies.get('userID') or ''
    secureUserID = request.cookies.get('secureUserID') or ''
    httpOnlyUserID = request.cookies.get('httpOnlyUserID') or ''
    return f"""
    <h1>userID: {userID}</h1>
    <h1>secureUserID: {secureUserID}</h1>
    <h1>httpOnlyUserID: {httpOnlyUserID}</h1>
    """