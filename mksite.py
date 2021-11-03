#!/usr/bin/env python3

import csv
import feedparser
import os
import re
import sys
import textwrap
from urllib.parse import urlparse
import yaml
import http

def find_atom_link(feed):
    for link in feed.channel.get('links', []):
        if link.type == 'application/atom+xml':
            return link.href
    return None


def is_language_learning(feed):
    for tag in feed.channel.get('tags', []):
        if tag.term == 'Language Learning':
            return True
    return False


def read_podcast(rss_url):
    print('feed', rss_url)
    d = feedparser.parse(rss_url)
    print(' - # RSS posts :', len(d.entries))

    atom_link = find_atom_link(d)
    if not atom_link:
        print("NO ATOM LINK")
        return

    print(" - atom", atom_link)
    id = re.sub('^/xml(hd)?/', '', urlparse(atom_link).path).lower()
    print(" - id", id)

    print(' - deutschkurs', is_language_learning(d))

    dir = 'site/src/podcasts/'

    language = d.feed.language
    deutschkurs = is_language_learning(d)
    if deutschkurs:
        dir += 'deutschkurs/'
    else:
        dir += language

    page_link = re.sub('^http:', 'https:', d.feed.link)
    page_link = re.sub('dw\.de/', 'dw.com/', page_link)

    os.makedirs(dir, exist_ok=True)

    entries = {'entries': []}
    for e in d.entries:
        entries['entries'].append({
            'title': e.title,
            'link': e.link,
            'published': e.published,
            'summary': e.get('summary', None)
        })

    with open(f'{dir}/{id}.stx', 'w') as f:
        f.write(f'''---
title: "{d.feed.title}"
id: {id}
published: "{d.feed.published}"
page_link: "{page_link}"
atom_link: "{atom_link}"
language: {language}
deutschkurs: {deutschkurs}
category: "{d.feed.get('category', '')}"
tags: [ {', '.join(['"' + t.term + '"' for t in d.channel.get('tags', [])])} ]
image_url: {d.feed.image.href}
image_title: "{d.feed.image.get('title', '')}"
{yaml.dump(entries)}
---
{textwrap.fill(d.feed.description)}
''')


def read_podcasts(csv_filename):
    with open(csv_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
            rss_url = row[4].strip()
            if rss_url != '' and re.match('^https?:', rss_url):
                try:
                    read_podcast(rss_url)
                except http.client.IncompleteRead:
                    print("### IncompleteRead")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(f'Usage: {sys.argv[0]} <list of podcasts as TSV file>')
    read_podcasts(sys.argv[1])