"""Seed script for demo data (Articles, Users, WeatherData, Comments)

Run with: python3 scripts/seed_news.py
"""
from datetime import datetime
from app import app, db
from app.models import User, Article, WeatherData, Comment, Category


def seed():
    with app.app_context():
        # create tables if they don't exist
        db.create_all()

        # Create a sample user
        if not User.query.filter_by(username='seed_user').first():
            u = User(username='seed_user', email='seed_user@example.com')
            u.set_password('test')
            db.session.add(u)
            db.session.commit()
        else:
            u = User.query.filter_by(username='seed_user').first()

        # Create sample categories
        cat_names = ['World', 'Business', 'Technology']
        cats = []
        for name in cat_names:
            existing = Category.query.filter_by(name=name).first()
            if not existing:
                c = Category(name=name, description=f'{name} news')
                db.session.add(c)
                cats.append(c)
            else:
                cats.append(existing)
        db.session.commit()

        # Create sample articles
        articles = []
        for i, cat in enumerate(cats, start=1):
            art = Article(headline=f'Sample Article {i} - {cat.name}',
                          summary=f'Summary for {cat.name}',
                          body=f'Full body text for sample article {i}.',
                          category=cat.name,
                          image_url='https://ichef.bbci.co.uk/news/800/cpsprodpb/sample.jpg',
                          published_at=datetime.utcnow(),
                          author_id=u.id)
            db.session.add(art)
            articles.append(art)
        db.session.commit()

        # Add weather data
        if not WeatherData.query.first():
            w = WeatherData(city='London', today_temperature_high=18, today_temperature_low=12,
                            today_description='Partly Cloudy', today_icon='partly_cloudy')
            db.session.add(w)
            db.session.commit()

        # Add a comment to the first article
        if articles:
            first = articles[0]
            c = Comment(text='Great article, thanks!', user_id=u.id, article_id=first.id)
            db.session.add(c)
            db.session.commit()

        print('Seed complete: users=%s articles=%s' % (User.query.count(), Article.query.count()))


if __name__ == '__main__':
    seed()
