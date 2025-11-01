from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, g, jsonify, make_response, render_template_string
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse as url_parse
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
    # also fetch recent articles to show on the homepage
    try:
        articles = Article.query.order_by(Article.published_at.desc()).limit(6).all()
    except Exception:
        articles = []

    # pick a film/culture article to feature in the film-review block if available
    film_article_id = None
    try:
        film_article = Article.query.filter_by(category='Culture').order_by(Article.published_at.desc()).first()
        if film_article:
            film_article_id = film_article.id
    except Exception:
        film_article_id = None

    return render_template('index.html.j2', title=_('Latest News'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, articles=articles, film_article_id=film_article_id)


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
    # keep an article endpoint but render a simple category-first placeholder
    return render_template_string('<!doctype html><html><head><title>Article</title></head><body><h1>Article</h1></body></html>')

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



# init_db route removed to avoid exposing initialization in production.
# If you need to initialize DB during development, run a separate script
# or enable it conditionally behind a secure flag.

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
    # Optional query param for GET to show a specific article's comments
    if request.method == 'GET':
        article_id = request.args.get('article_id', type=int)
    else:
        # On POST, prefer article_id from the submitted form (HiddenField)
        article_id = None

    if article_id:
        comments = Comment.query.filter_by(article_id=article_id).order_by(Comment.date_posted.desc()).all()
    else:
        comments = Comment.query.order_by(Comment.date_posted.desc()).all()

    if form.validate_on_submit():
        text = form.comment.data
        # read article_id from form field when posting
        try:
            posted_article_id = None
            try:
                posted_article_id = int(form.article_id.data) if form.article_id.data else None
            except Exception:
                posted_article_id = None

            new_comment = Comment(text=text, user_id=current_user.id, article_id=posted_article_id)
            db.session.add(new_comment)
            db.session.commit()
            flash('Your comment has been posted!', 'success')
            # redirect back to the same context (article or general comment page)
            if posted_article_id:
                # When posting from an article detail page, return to the article view
                return redirect(url_for('article_detail', article_id=posted_article_id))
            return redirect(url_for('comment'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while posting your comment. Please try again.', 'danger')
            # If this post was for a specific article, render that article page with the form and errors
            if posted_article_id:
                try:
                    art = Article.query.get(posted_article_id)
                    art_comments = Comment.query.filter_by(article_id=posted_article_id).order_by(Comment.date_posted.desc()).all()
                    return render_template('article_detail.html.j2', article=art, comments=art_comments, form=form, title=art.headline)
                except Exception:
                    pass
            return render_template('comment.html.j2', comments=comments, form=form, title='Comments')

    return render_template('comment.html.j2', comments=comments, form=form, title='Comments')


@app.route('/article/<int:article_id>', methods=['GET'])
@login_required
def article_detail(article_id):
    # Show an article and its comments; use Article.html.j2 as a simple detail view
    article = Article.query.get_or_404(article_id)
    comments = Comment.query.filter_by(article_id=article_id).order_by(Comment.date_posted.desc()).all()
    form = CommentForm()
    return render_template('article_detail.html.j2', article=article, comments=comments, form=form, title=article.headline)

@app.route('/ArticleA')
@login_required
def ArticleA():
    return render_template('World.html.j2', title='World')


@app.route('/World')
@login_required
def World():
    # new route alias for ArticleA content under category 'World'
    return render_template('World.html.j2', title='World')

@app.route('/ArticleB')
@login_required
def ArticleB():
    return render_template('Business.html.j2', title='Business')


@app.route('/Business')
@login_required
def Business():
    return render_template('Business.html.j2', title='Business')

@app.route('/ArticleC')
@login_required
def ArticleC():
    return render_template('Technology.html.j2', title='Technology')


@app.route('/Technology')
@login_required
def Technology():
    return render_template('Technology.html.j2', title='Technology')

@app.route('/ArticleD')
@login_required
def ArticleD():
    return render_template('Sport.html.j2', title='Sport')


@app.route('/Sport')
@login_required
def Sport():
    return render_template('Sport.html.j2', title='Sport')

@app.route('/ArticleE')
@login_required
def ArticleE():
    return render_template('Culture.html.j2', title='Culture')


@app.route('/Culture')
@login_required
def Culture():
    return render_template('Culture.html.j2', title='Culture')

@app.route('/ArticleF')
@login_required
def ArticleF():
    return render_template('Opinion.html.j2', title='Opinion')


@app.route('/Opinion')
@login_required
def Opinion():
    return render_template('Opinion.html.j2', title='Opinion')

@app.errorhandler(404)
def page_not_found(e):  
    return render_template('404.html.j2', title='404'), 404

@app.route('/test_500')
def internal_server_error():
    return render_template('500.html.j2', title='500'), 500

@app.route('/setcookie', methods=['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        user = request.form.get('nm', '')  # 'nm' is the form field name
        resp = make_response(render_template('readcookie.html.j2', user=user))
        # Use the imported datetime and timedelta correctly
        expire_date = datetime.now() + timedelta(seconds=5)
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