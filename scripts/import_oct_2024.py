"""Import BBC October 2024 articles (sample or fetched) into the app.

Features:
- Fetch BBC RSS feeds and filter items from October 2024 (--fetch)
- Dry-run by default: print what would be imported without writing DB or calling AWS
- Optional AWS integration: upload images to S3, write metadata to DynamoDB, send SQS messages (--aws)
- Optional commit to DB (--commit)

Usage examples:
  python3 scripts/import_oct_2024.py --fetch            # fetch live BBC feeds, dry-run
  python3 scripts/import_oct_2024.py --fetch --commit   # fetch and write to DB
  python3 scripts/import_oct_2024.py --aws --commit     # use SAMPLE_ARTICLES, upload images and send messages
"""

from datetime import datetime
import argparse
import os
import sys
import tempfile
import json

import requests

# ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import Article, User

try:
    import feedparser
    HAVE_FEEDPARSER = True
except Exception:
    feedparser = None
    HAVE_FEEDPARSER = False

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    HAVE_BOTO3 = True
except Exception:
    boto3 = None
    HAVE_BOTO3 = False


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


def fetch_bbc_oct_2024(limit_feeds=None):
    """Fetch BBC RSS feeds and return items published in Oct 2024.

    Uses feedparser if available; otherwise returns empty list and logs a hint.
    """
    feeds = [
        'http://feeds.bbci.co.uk/news/rss.xml',
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'http://feeds.bbci.co.uk/news/technology/rss.xml',
        'http://feeds.bbci.co.uk/news/business/rss.xml',
        'http://feeds.bbci.co.uk/news/uk/rss.xml',
    ]
    items = []
    if not HAVE_FEEDPARSER:
        print('feedparser not installed — cannot fetch BBC RSS. Install feedparser or run with --no-fetch to use samples.')
        return items

    for url in (feeds[:limit_feeds] if limit_feeds else feeds):
        d = feedparser.parse(url)
        for e in d.entries:
            # many entries have published_parsed
            pub = None
            try:
                if hasattr(e, 'published_parsed') and e.published_parsed:
                    pub = datetime(*e.published_parsed[:6])
                elif hasattr(e, 'published'):
                    pub = datetime.strptime(e.published, '%a, %d %b %Y %H:%M:%S %Z')
            except Exception:
                pub = None
            if not pub:
                continue
            if pub.year == 2024 and pub.month == 10:
                # try to extract image
                image = None
                if 'media_thumbnail' in e:
                    try:
                        image = e.media_thumbnail[0]['url']
                    except Exception:
                        image = None
                if not image and 'media_content' in e:
                    try:
                        image = e.media_content[0]['url']
                    except Exception:
                        image = None
                items.append({
                    'headline': e.title,
                    'summary': getattr(e, 'summary', '')[:300],
                    'body': getattr(e, 'summary', ''),
                    'category': getattr(e, 'category', '') if hasattr(e, 'category') else 'World',
                    'image_url': image,
                    'published_at': pub,
                    'link': getattr(e, 'link', None)
                })
    # dedupe by headline
    seen = set()
    filtered = []
    for it in items:
        if it['headline'] in seen:
            continue
        seen.add(it['headline'])
        filtered.append(it)
    return filtered


def download_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        suffix = os.path.splitext(url.split('?')[0])[1] or '.jpg'
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as f:
            f.write(r.content)
        return path
    except Exception as e:
        print(f'Image download failed for {url}: {e}')
        return None


def aws_upload_image_to_s3(s3_client, bucket, key, local_path):
    try:
        with open(local_path, 'rb') as f:
            s3_client.put_object(Bucket=bucket, Key=key, Body=f)
        return True
    except Exception as e:
        print(f'Failed to upload to S3 {bucket}/{key}: {e}')
        return False


def aws_write_dynamodb(ddb_client, table_name, item):
    try:
        ddb_client.put_item(TableName=table_name, Item=item)
        return True
    except Exception as e:
        print(f'Failed to write DynamoDB item to {table_name}: {e}')
        return False


def aws_send_sqs(sqs_client, queue_url, message_body):
    try:
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
        return True
    except Exception as e:
        print(f'Failed to send SQS message to {queue_url}: {e}')
        return False


def import_articles(articles, commit=False, aws=False, aws_opts=None):
    """Import or dry-run the provided articles list.

    articles: list of dicts with keys headline, summary, body, category, image_url, published_at
    commit: if True, write to DB
    aws: if True, attempt AWS operations using aws_opts dict (s3_bucket, dynamo_table, sqs_queue)
    """
    with app.app_context():
        author = ensure_author()
        created = []
        for a in articles:
            existing = Article.query.filter_by(headline=a['headline']).first()
            if existing:
                print(f"Skipping existing: {existing.headline}")
                continue

            print(f"Preparing article: {a['headline']} ({a.get('published_at')})")
            if aws and HAVE_BOTO3 and a.get('image_url'):
                # download image and upload to s3
                local = download_image(a['image_url'])
                if local:
                    s3 = boto3.client('s3')
                    key = f"articles/{os.path.basename(local)}"
                    uploaded = aws_upload_image_to_s3(s3, aws_opts.get('s3_bucket'), key, local)
                    if uploaded:
                        # replace image_url with s3 path
                        a['image_url'] = f"s3://{aws_opts.get('s3_bucket')}/{key}"
                    try:
                        os.remove(local)
                    except Exception:
                        pass

            if commit:
                art = Article(
                    headline=a['headline'],
                    summary=a.get('summary') or '',
                    body=a.get('body') or '',
                    category=a.get('category') or 'World',
                    image_url=a.get('image_url'),
                    published_at=a.get('published_at') or datetime.utcnow(),
                    author=author
                )
                db.session.add(art)
                created.append(art)
            else:
                # dry-run: show a small summary
                print(f"DRY RUN -> would create: {a['headline']} ({a.get('category')}) image: {a.get('image_url')}")

            # AWS DynamoDB and SQS operations (best-effort)
            if aws and HAVE_BOTO3:
                # DynamoDB
                if aws_opts.get('dynamo_table'):
                    ddb = boto3.client('dynamodb')
                    # DynamoDB expects a typed Item; keep it simple with strings
                    item = {
                        'headline': {'S': a['headline']},
                        'category': {'S': a.get('category', 'World')},
                        'published_at': {'S': str(a.get('published_at'))}
                    }
                    aws_write_dynamodb(ddb, aws_opts.get('dynamo_table'), item)

                # SQS
                if aws_opts.get('sqs_queue'):
                    sqs = boto3.client('sqs')
                    payload = {'headline': a['headline'], 'link': a.get('link')}
                    aws_send_sqs(sqs, aws_opts.get('sqs_queue'), payload)

        if commit and created:
            db.session.commit()
            print(f"Imported {len(created)} articles to DB")
            for c in created:
                print(f" - {c.headline} ({c.published_at})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fetch', action='store_true', help='Fetch BBC RSS and filter Oct 2024 items')
    p.add_argument('--limit-feeds', type=int, default=None, help='Limit number of feeds to fetch (for testing)')
    p.add_argument('--commit', action='store_true', help='Commit changes to the database')
    p.add_argument('--aws', action='store_true', help='Attempt AWS operations (requires boto3/credentials)')
    p.add_argument('--s3-bucket', default=os.environ.get('AWS_S3_BUCKET'), help='S3 bucket name')
    p.add_argument('--dynamo-table', default=os.environ.get('AWS_DYNAMO_TABLE'), help='DynamoDB table name')
    p.add_argument('--sqs-queue', default=os.environ.get('AWS_SQS_QUEUE'), help='SQS queue URL')
    p.add_argument('--dry-run', dest='dry_run', action='store_true', help='Explicit dry run (default)')
    p.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='Disable dry run; equivalent to --commit')
    p.set_defaults(dry_run=True)

    args = p.parse_args()

    articles = []
    if args.fetch:
        print('Fetching BBC RSS for Oct 2024...')
        articles = fetch_bbc_oct_2024(limit_feeds=args.limit_feeds)
        print(f'Found {len(articles)} items from BBC feeds (Oct 2024)')
    else:
        articles = SAMPLE_ARTICLES

    aws_opts = {'s3_bucket': args.s3_bucket, 'dynamo_table': args.dynamo_table, 'sqs_queue': args.sqs_queue}

    # dry_run is True by default; commit implies dry_run False
    commit = args.commit or (not args.dry_run and args.commit)
    # if user passed --no-dry-run, but not --commit, interpret as commit
    if not args.dry_run and not args.commit:
        commit = True

    import_articles(articles, commit=commit, aws=args.aws, aws_opts=aws_opts)


if __name__ == '__main__':
    main()
