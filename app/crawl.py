#!/usr/bin/env python

import logging
logger = logging.getLogger('crawl')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s %(message)s')
sh.setFormatter(fmt)
logger.addHandler(sh)

from bs4 import BeautifulSoup
import requests

from models import db
from models import QueuedUrl
from models import Url


def spider(qurl, content):
    logger.info('Spidering: %s' % qurl)
    soup = BeautifulSoup(content)

    level = qurl.level + 1

    for elem in soup.find_all('a'):
        url = elem.get('href')
        enqueue_new({
            'parent_url': qurl.url,
            'url': url,
            'context': 'anchor',
            'level': level,
        })

    for elem in soup.find_all('link'):
        url = elem.get('href')
        enqueue_new({
            'parent_url': qurl.url,
            'url': url,
            'context': 'link',
            'level': level,
        })

    for elem in soup.find_all('script'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': url,
            'context': 'script',
            'level': level,
        })

    for elem in soup.find_all('img'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': url,
            'context': 'img',
            'level': level,
        })

    for elem in soup.find_all('iframe'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': url,
            'context': 'iframe',
            'level': level,
        })

def enqueue_new(dct):
    qurl = QueuedUrl(**dct)
    db.session.add(qurl)
    db.session.commit()

def dequeue_next():
    qurl = QueuedUrl.query.first()
    if qurl:
        logger.info('Dequeued: %s' % qurl)
        QueuedUrl.query.filter(QueuedUrl.id == qurl.id).delete()
        db.session.commit()
        return qurl

def store_url(qurl, status_code):
    logger.info('Storing: %s' % qurl)

    parent = None
    if qurl.parent_url:
        parent = Url.query.filter(Url.url == qurl.parent_url).first()

    url = Url(
        url=qurl.url,
        level=qurl.level,
        context=qurl.context,
        status_code=status_code,
        parent=parent,
    )
    db.session.add(url)
    db.session.commit()

def main():
    qurl = dequeue_next()
    while qurl:
        logger.info('Fetching: %s' % qurl)
        r = requests.get(qurl.url)
        content = r.text

        spider(qurl, content)
        store_url(qurl, r.status_code)

        qurl = dequeue_next()


if __name__ == '__main__':
    import os
    if os.path.isfile('store.sqlite'):
        os.unlink('store.sqlite')

    db.create_all()
    qurl = QueuedUrl(url='http://www.juventuz.net', level=0)
    db.session.add(qurl)
    db.session.commit()

    main()
