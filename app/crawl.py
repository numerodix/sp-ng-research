#!/usr/bin/env python

import logging
logger = logging.getLogger('crawl')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s %(message)s')
sh.setFormatter(fmt)
logger.addHandler(sh)

import os
import re
import urlparse

from bs4 import BeautifulSoup
import requests

from models import app
from models import db
from models import QueuedUrl
from models import Url


def urljoin(url, path):
    url_new = path
    if path:
        if not path.startswith('http'):
            url_new = urlparse.urljoin(url, path)
            url_new = re.sub('../', '', url_new)
    return url_new

def spider(qurl, content):
    logger.info('Spidering: %s' % qurl)
    soup = BeautifulSoup(content)

    level = qurl.level + 1

    for elem in soup.find_all('a'):
        url = elem.get('href')
        enqueue_new({
            'parent_url': qurl.url,
            'url': urljoin(qurl.url, url),
            'context': 'anchor',
            'level': level,
        })

    for elem in soup.find_all('link'):
        url = elem.get('href')
        enqueue_new({
            'parent_url': qurl.url,
            'url': urljoin(qurl.url, url),
            'context': 'link',
            'level': level,
        })

    for elem in soup.find_all('script'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': urljoin(qurl.url, url),
            'context': 'script',
            'level': level,
        })

    for elem in soup.find_all('img'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': urljoin(qurl.url, url),
            'context': 'img',
            'level': level,
        })

    for elem in soup.find_all('iframe'):
        url = elem.get('src')
        enqueue_new({
            'parent_url': qurl.url,
            'url': urljoin(qurl.url, url),
            'context': 'iframe',
            'level': level,
        })

def enqueue_new(dct):
    url = dct.get('url')
    if url and url.startswith('http://www.juventuz.net'):
        if (not QueuedUrl.query.filter(QueuedUrl.url == url).first()
            and (not Url.query.filter(Url.url == url).first())):
            qurl = QueuedUrl(**dct)
            db.session.add(qurl)
            db.session.commit()
            logger.info('Enqueued: %s' % qurl)

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
    logger.info('Stored: %s' % url)

def main():
    qurl = dequeue_next()
    while qurl:
        if qurl.context == 'anchor':
            logger.info('Fetching: %s' % qurl)
            r = requests.get(qurl.url)
            content = r.text

            spider(qurl, content)

        store_url(qurl, r.status_code)

        qurl = dequeue_next()


if __name__ == '__main__':
    logger.info('Preparing datastore')
    db_driver = app.config['SQLALCHEMY_DATABASE_URI']
    if db_driver.startswith('sqlite'):
        if os.path.isfile('store.sqlite'):
            os.unlink('store.sqlite')
    elif db_driver.startswith('postgresql'):
        os.system('dropdb crawl')
        os.system('createdb crawl')

    logger.info('Creating models')
    db.create_all()

    enqueue_new(dict(url='http://www.juventuz.net', level=0, context='anchor'))

    logger.info('Starting main()')
    main()
