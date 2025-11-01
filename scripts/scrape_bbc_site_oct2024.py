"""Attempt to search BBC site for Oct 2024 articles and return 5 sample items (dry-run).

This uses Wayback-discovered article links as seeds and fetches the archived page
content, then extracts a headline and first paragraph heuristically for a dry-run.
"""
import sys
import os
import re
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import scripts.fetch_wayback_oct2024 as way
import requests


def extract_headline_and_summary(html):
    """Use BeautifulSoup to extract a clean headline and a short summary/body.

    Strategy:
    - headline: first <h1> text
    - paragraphs: prefer paragraphs within an <article> tag or within main content
      otherwise fall back to first visible <p> tags. Join the first 1-3 paragraphs
      to produce a short summary and a longer body.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception:
        # fallback to regex-based extraction (best-effort)
        h = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        p = re.search(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
        headline = h.group(1).strip() if h else None
        summary = p.group(1).strip() if p else None
        headline = re.sub('<[^<]+?>', '', headline) if headline else None
        summary = re.sub('<[^<]+?>', '', summary) if summary else None
        return headline, summary

    # headline
    h1 = soup.find('h1')
    headline = h1.get_text(separator=' ', strip=True) if h1 else None

    # find candidate paragraphs inside article or main
    paragraphs = []
    article_tag = soup.find('article')
    if article_tag:
        paragraphs = [p.get_text(separator=' ', strip=True) for p in article_tag.find_all('p') if p.get_text(strip=True)]
    if not paragraphs:
        # look for a main/content container
        main = soup.find('main') or soup.find(attrs={"role": "main"})
        if main:
            paragraphs = [p.get_text(separator=' ', strip=True) for p in main.find_all('p') if p.get_text(strip=True)]
    if not paragraphs:
        # fallback: any top-level <p>
        paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]

    # build summary (first 1-2 paras) and body (first up to 6 paras)
    summary = ' '.join(paragraphs[:2]) if paragraphs else None
    body = ' '.join(paragraphs[:6]) if paragraphs else None

    # extra-clean whitespace
    if headline:
        headline = re.sub(r"\s+", ' ', headline).strip()
    if summary:
        summary = re.sub(r"\s+", ' ', summary).strip()

    return headline, summary


def main():
    print('Finding archived RSS snapshots (Wayback) to seed article links...')
    archives = way.find_archives(limit=5)
    links = []
    for a in archives:
        try:
            content = way.fetch_archived_feed(a['timestamp'], a['original'])
            items = way.parse_feed(content)
            for it in items:
                if it['published'] and it['published'].year == 2024 and it['published'].month == 10 and it.get('link'):
                    links.append({'timestamp': a['timestamp'], 'link': it['link']})
        except Exception as e:
            print('archive fetch failed', e)
    # take up to 5 unique links
    seen = set()
    unique = []
    for l in links:
        if l['link'] in seen:
            continue
        seen.add(l['link'])
        unique.append(l)
        if len(unique) >= 5:
            break
    print(f'Found {len(unique)} article links to fetch')
    samples = []
    for u in unique:
        archived_url = f"https://web.archive.org/web/{u['timestamp']}/{u['link']}"
        try:
            r = requests.get(archived_url, timeout=20)
            r.raise_for_status()
            h, s = extract_headline_and_summary(r.text)
            samples.append({'link': u['link'], 'archived_url': archived_url, 'headline': h, 'summary': s})
        except Exception as e:
            print('fetch article failed', archived_url, e)
    print('Sampled articles:')
    for s in samples:
        print('-', s['headline'], s['archived_url'])
        print('  summary:', (s['summary'] or '')[:200])

if __name__ == '__main__':
    main()
