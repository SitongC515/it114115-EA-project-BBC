"""Fetch BBC RSS from Wayback (Oct 2024) and list articles.

Usage: python3 scripts/fetch_wayback_oct2024.py

This script queries the Internet Archive CDX API for archived copies of the BBC
RSS feed in October 2024, downloads up to a few snapshots, parses the RSS with
feedparser and prints headlines found that were published in Oct 2024.
"""
import requests
import json
from datetime import datetime
import feedparser

CDX_URL = 'http://web.archive.org/cdx/search/cdx'
FEED_URL = 'http://feeds.bbci.co.uk/news/rss.xml'

def find_archives(from_date='20241001', to_date='20241031', limit=5):
    params = {
        'url': FEED_URL,
        'from': from_date,
        'to': to_date,
        'output': 'json',
        'filter': 'statuscode:200',
        'fl': 'timestamp,original',
        'collapse': 'digest'
    }
    r = requests.get(CDX_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    # first row is header if any
    if not data or len(data) < 2:
        return []
    rows = data[1:limit+1]
    results = [{'timestamp': row[0], 'original': row[1]} for row in rows]
    return results


def fetch_archived_feed(timestamp, original):
    url = f'https://web.archive.org/web/{timestamp}/{original}'
    print(f'Downloading archived feed: {url}')
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def parse_feed(content):
    parsed = feedparser.parse(content)
    items = []
    for e in parsed.entries:
        pub = None
        try:
            if hasattr(e, 'published_parsed') and e.published_parsed:
                pub = datetime(*e.published_parsed[:6])
        except Exception:
            pub = None
        items.append({'title': getattr(e, 'title', None), 'published': pub, 'link': getattr(e, 'link', None)})
    return items


def main():
    print('Querying Wayback CDX for BBC RSS (Oct 2024) ...')
    archives = find_archives()
    if not archives:
        print('No archived RSS snapshots found for Oct 2024 via CDX.')
        return
    found = []
    for a in archives:
        try:
            content = fetch_archived_feed(a['timestamp'], a['original'])
            items = parse_feed(content)
            for it in items:
                if it['published'] and it['published'].year == 2024 and it['published'].month == 10:
                    found.append(it)
        except Exception as e:
            print('Failed to fetch or parse archive', a, e)
    # dedupe by title
    seen = set()
    unique = []
    for it in found:
        if it['title'] in seen:
            continue
        seen.add(it['title'])
        unique.append(it)
    print(f'Found {len(unique)} unique Oct 2024 items from Wayback RSS snapshots:')
    for it in unique:
        print('-', it['published'], it['title'], it['link'])

if __name__ == '__main__':
    main()
