"""Commit articles discovered via Wayback RSS snapshots into the app database.

Usage: python3 scripts/commit_wayback_to_db.py

This script will find archived BBC RSS snapshots for Oct 2024 (using existing
helpers in fetch_wayback_oct2024.py), build article dicts and insert them into
the application's DB (skipping existing headlines).
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import Article, User
import scripts.fetch_wayback_oct2024 as way


def ensure_author():
    user = User.query.filter_by(username='newsbot').first()
    if not user:
        user = User(username='newsbot', email='newsbot@example.com')
        user.set_password('newsbot')
        db.session.add(user)
        db.session.commit()
    return user


def build_articles_from_wayback(limit=5):
    archives = way.find_archives(limit=5)
    articles = []
    for a in archives:
        try:
            content = way.fetch_archived_feed(a['timestamp'], a['original'])
            items = way.parse_feed(content)
            for it in items:
                if it['published'] and it['published'].year == 2024 and it['published'].month == 10:
                    articles.append({
                        'headline': it['title'],
                        'summary': '',
                        'body': '',
                        'category': 'World',
                        'image_url': None,
                        'published_at': it['published'],
                        'link': it.get('link')
                    })
        except Exception as e:
            print('failed archive', a, e)
    # dedupe by headline
    seen = set()
    uniq = []
    for it in articles:
        if not it['headline'] or it['headline'] in seen:
            continue
        seen.add(it['headline'])
        uniq.append(it)
    return uniq


if __name__ == '__main__':
    with app.app_context():
        author = ensure_author()
        arts = build_articles_from_wayback(limit=10)  # use up to 10 snapshots to gather items
        print(f'Committing {len(arts)} articles (skip existing headlines)')
        added = 0
        for a in arts:
            if Article.query.filter_by(headline=a['headline']).first():
                print('skip exists:', a['headline'])
                continue
            art = Article(
                headline=a['headline'] or 'No headline',
                summary=a.get('summary') or '',
                body=a.get('body') or '',
                category=a.get('category') or 'World',
                image_url=a.get('image_url'),
                published_at=a.get('published_at') or datetime.utcnow(),
                author=author
            )
            db.session.add(art)
            added += 1
        if added:
            db.session.commit()
        print('Done. Added:', added)
