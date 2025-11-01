"""Import sample BBC October 2024 articles into the app database.

This script can be run with: python3 scripts/import_oct_2024.py
It uses the application's app context and SQLAlchemy models.
"""
from datetime import datetime
import os
import sys

# Ensure project root is on sys.path so 'app' package can be imported when
# running this script directly from the scripts/ folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import Article, User

SAMPLE_ARTICLES = [
    {
        "headline": "Global markets react to new fiscal policies",
        "summary": "Markets shifted after major fiscal announcements across regions.",
        "body": "Detailed reporting about markets and policy shifts...",
        "category": "Business",
        "image_url": "https://ichef.bbci.co.uk/news/800/cpsprodpb/sample1.jpg",
        "published_at": datetime(2024, 10, 5, 9, 30)
    },
    {
        "headline": "Breakthrough in renewable energy storage unveiled",
        "summary": "Researchers announce a leap forward in battery tech.",
        "body": "Teams from multiple universities demonstrate improved density and charging cycles...",
        "category": "Technology",
        "image_url": "https://ichef.bbci.co.uk/news/800/cpsprodpb/sample2.jpg",
        "published_at": datetime(2024, 10, 12, 14, 0)
    },
    {
        "headline": "Historic peace talks show early signs of progress",
        "summary": "Delegates report initial agreement on humanitarian corridors.",
        "body": "Negotiators have laid groundwork for sustained ceasefire measures...",
        "category": "World",
        "image_url": "https://ichef.bbci.co.uk/news/800/cpsprodpb/sample3.jpg",
        "published_at": datetime(2024, 10, 19, 8, 45)
    }
]


def ensure_author():
    # create or return a demo author user
    user = User.query.filter_by(username='newsbot').first()
    if not user:
        user = User(username='newsbot', email='newsbot@example.com')
        user.set_password('newsbot')
        db.session.add(user)
        db.session.commit()
    return user


def import_articles():
    with app.app_context():
        author = ensure_author()
        created = []
        for a in SAMPLE_ARTICLES:
            existing = Article.query.filter_by(headline=a['headline']).first()
            if existing:
                print(f"Skipping existing: {existing.headline}")
                continue
            art = Article(
                headline=a['headline'],
                summary=a['summary'],
                body=a['body'],
                category=a['category'],
                image_url=a['image_url'],
                published_at=a['published_at'],
                author=author
            )
            db.session.add(art)
            created.append(art)
        db.session.commit()
        print(f"Imported {len(created)} articles")
        for c in created:
            print(f" - {c.headline} ({c.published_at})")


if __name__ == '__main__':
    import_articles()
