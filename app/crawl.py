#!/usr/bin/env python

import os
import re
import sys
import urlparse

from bs4 import BeautifulSoup
import requests

from models import app
from models import db
from models import QueuedUrl
from models import Url

import logutils
logger = logutils.getLogger('crawl')


class Fetcher(object):
    def __init__(self, url):
        self.url = url
        self.request = None

    def fetch(self):
        return
        self.request = requests.Request(url=self.url)

    def get_content(self):
        pass


class Crawler(object):
    def __init__(self, host):
        self.host = host
        self.enqueue_new(None, dict(url=self.host, level=0, context='anchor'))

    def urljoin(self, url, path):
        url_new = path
        if path:
            if not path.startswith('http'):
                url_new = urlparse.urljoin(url, path)
                url_new = re.sub('#.*$', '', url_new)  # remove fragment
                url_new = re.sub('[.]{2}\/', '', url_new)
        return url_new

    def spider(self, qurl, content):
        logger.info('Spidering: %s' % qurl)
        soup = BeautifulSoup(content)

        level = qurl.level + 1

        def enqueue(url, context):
            self.enqueue_new(qurl, {
                'parent_url': qurl.url,
                'url': self.urljoin(qurl.url, url),
                'context': context,
                'level': level,
            })

        for elem in soup.find_all('a'):
            url = elem.get('href')
            enqueue(url, 'anchor')

        for elem in soup.find_all('link'):
            url = elem.get('href')
            enqueue(url, 'link')

        for elem in soup.find_all('script'):
            url = elem.get('src')
            enqueue(url, 'script')

        for elem in soup.find_all('img'):
            url = elem.get('src')
            enqueue(url, 'img')

        for elem in soup.find_all('iframe'):
            url = elem.get('src')
            enqueue(url, 'iframe')

        for elem in soup.find_all('embed'):
            url = elem.get('src')
            enqueue(url, 'embed')

    def enqueue_new(self, parent, dct):
        url = dct.get('url')
        #logger.info('Enqueuing: %s' % url)

        if not url:
            return
        if url == 'None':
            return
        # improve match to: by top level domain
        if not (url.startswith(self.host) or url.startswith(self.host.replace('www.', ''))):
            return
        if parent and url == parent.url:
            return
        if (QueuedUrl.query.filter(QueuedUrl.url == url).first()
            or Url.query.filter(Url.url == url).first()):
            return

        qurl = QueuedUrl(**dct)
        db.session.add(qurl)
        db.session.commit()
        logger.info('Enqueued: %s' % qurl)

    def dequeue_next(self):
        qurl = QueuedUrl.query.first()
        if qurl:
            logger.info('Dequeued: %s' % qurl)
            QueuedUrl.query.filter(QueuedUrl.id == qurl.id).delete()
            db.session.commit()
            return qurl

    def store_url(self, qurl, status_code):
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

    def main(self):
        qurl = self.dequeue_next()
        while qurl:
            if qurl.context == 'anchor':
                logger.info('Fetching: %s' % qurl)
                fetcher = Fetcher(qurl.url)
                content = fetcher.get_content()

                self.spider(qurl, content)

            self.store_url(qurl, status_code)

            qurl = self.dequeue_next()


if __name__ == '__main__':
    host = sys.argv[1]

    logger.info('Preparing datastore')
    db_driver = app.config['SQLALCHEMY_DATABASE_URI']
    if db_driver.startswith('sqlite'):
        if os.path.isfile('store.sqlite'):
            os.unlink('store.sqlite')
    elif db_driver.startswith('postgresql'):
        os.system('sudo /etc/init.d/postgresql restart')
        os.system('dropdb crawl')
        os.system('createdb crawl')

    logger.info('Creating models')
    db.create_all()

    logger.info('Starting main()')
    crawler = Crawler(host)
    crawler.main()
