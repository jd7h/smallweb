import datetime
import io

import feedparser
import feedwerk
import requests
import pytz

from feedwerk.atom import AtomFeed
from dateutil import parser as dateutil_parser

from loguru import logger

logger.remove()
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
            logger.debug(str(post))
    return feed

def main():
    with open(FEEDFILE, 'r') as infile:
        feeds = [f.strip() for f in infile.readlines()]

    collected_entries = []
    for feedlink in feeds:
        logger.info(f"Scraping feed url {feedlink}")
        # we parse the feed in two steps instead of with feedparser.parse
        # because parse() occassionally hangs without feedback
        try:
            response = requests.get(feedlink, timeout=5)
        except Exception as e:
            logger.error(e)
            continue
        if not response.ok:
            continue
        logger.info(f"Parsing feed url {feedlink}")
        try:
            d = feedparser.parse(io.BytesIO(response.content))
        except Exception as e:
            logger.error(e)
            continue
        for entry in list(d.entries):
            # fix missing authors
            if not entry.get('author'):
                entry['author'] = d['feed'].get('author') or ''
            if not entry.get('title'):
                entry['title'] = "-"
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
