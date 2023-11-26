import datetime

import feedparser
import feedwerk
import requests
import pytz

from feedwerk.atom import AtomFeed
from dateutil import parser as dateutil_parser

from loguru import logger

logger.add("small_web_feed.log")

FEEDFILE = "../smallweb-nl.txt"
MAX_AGE = datetime.timedelta(days=180)
MAX_ENTRIES = 100

FEED_NAME = "Small Web NL"
FEED_URL = "https://jd7h.com/smallweb-nl"


OUTFILE = "atom.xml"

now = datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))

# source: https://github.com/uniphil/feedwerk/blob/main/feedwerk/atom.py
def atom_feed(posts):
    feed = AtomFeed(title=FEED_NAME, title_type='text',
                    url=FEED_URL)
    for post in posts:
        try:
            feed.add(title=post.get('title'), id=post.get('link'), updated=post.get('updated_dt'), published=post.get('published_dt'), author=post.get('author'))
        except Exception as e:
            logger.error(e)
    #return feed.get_response()
    return feed

def main():
    with open(FEEDFILE, 'r') as infile:
        feeds = [f.strip() for f in infile.readlines()]

    collected_entries = []
    for feedlink in feeds:
        logger.info(f"Parsing feed url {feedlink}")
        d = feedparser.parse(feedlink)
        for entry in list(d.entries):
            # fix missing authors
            if not entry.get('author'):
                entry['author'] = d['feed'].get('author') or ''

            # fix datetimes
            entry['published_dt'] = dateutil_parser.parse(entry["published"])
            entry['updated_dt'] = dateutil_parser.parse(entry["updated"])
            if entry['published_dt'] > (now - MAX_AGE):
                collected_entries.append(entry)

    collected_entries.sort(key=lambda entry: entry.get('updated_dt'), reverse=True)
    collected_entries = collected_entries[:MAX_ENTRIES]

    feed = atom_feed(collected_entries)
    
    with open(OUTFILE, 'w') as outfile:
        outfile.write(feed.to_string())

    return feeds, collected_entries, feed

if __name__=='__main__':
    main()
