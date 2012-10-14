from multiprocessing.queues import Empty
import os
import re
import time
import urlparse

from bs4 import BeautifulSoup

from app import db
from models import QueuedResource
from models import Resource

from workerbase import Worker


def urljoin(url, path):
    url_new = path
    if path:
        if not path.startswith('http'):
            url_new = urlparse.urljoin(url, path)
            url_new = re.sub('#.*$', '', url_new)  # remove fragment
            url_new = re.sub('[.]{2}\/', '', url_new)  # remove excessive ../
    return url_new

class DbWorker(Worker):
    def __init__(self, fetch_queue, fetch_results, seed_urls=None, fetch_queue_preload=1):
        # init multiproc data structures
        self.fetch_queue = fetch_queue
        self.fetch_results = fetch_results
        self.seed_urls = seed_urls
        self.host = self.seed_urls[0]
        self.fetch_queue_preload = fetch_queue_preload

        # call base, dispatches to .mainloop
        super(DbWorker, self).__init__()

    def init_db(self):
        self.logger.info('Preparing datastore')

        os.system('sudo /etc/init.d/postgresql restart')
        os.system('dropdb crawl')
        os.system('createdb crawl')

        self.logger.info('Creating models')
        db.create_all()

    def seed_queue(self, urls):
        for url in urls:
            qres = QueuedResource(
                url=url,
                level=0,
            )
            db.session.add(qres)
        db.session.commit()

    def dequeue_next_qres(self):
        qres = QueuedResource.query.filter(
            QueuedResource.processing_status == 'new',
        ).first()
        if qres:
            self.logger.debug('Dequeued: %s' % qres)
            QueuedResource.query.filter(QueuedResource.id == qres.id).update({
                'processing_status': 'fetchable'
            })
            db.session.expunge_all()
            db.session.commit()
            return qres

    def store_new_url(self, msg):
        qres = msg['qres']
        res = msg['res']
        filepath = msg['filepath']

        self.logger.debug("Storing: %s" % res)
        res.content_length = os.path.getsize(filepath)
        if qres.parent_url:
            res.parent = Resource.query.filter(Resource.url == qres.parent_url).first()

        db.session.add(res)
        QueuedResource.query.filter(QueuedResource.id == qres.id).delete()
        db.session.commit()

        content = open(filepath).read()
        os.unlink(filepath)
        self.spider(qres, content)

    def spider(self, qres, content):
        self.logger.info('Spidering: %s' % qres)
        soup = BeautifulSoup(content)

        level = qres.level + 1

        def enqueue(url, context):
            self.enqueue_new_qres(qres, {
                'parent_url': qres.url,
                'url': urljoin(qres.url, url),
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

    def enqueue_new_qres(self, parent, dct):
        url = dct.get('url')
        #self.logger.debug('Enqueuing: %s' % url)

        if not url:
            return
        if url == 'None':
            return
        # improve match to: by top level domain
        if not (url.startswith(self.host) or url.startswith(self.host.replace('www.', ''))):
            return
        if parent and url == parent.url:
            return
        if (QueuedResource.query.filter(QueuedResource.url == url).first()
            or Resource.query.filter(Resource.url == url).first()):
            return

        qres = QueuedResource(**dct)
        db.session.add(qres)
        db.session.commit()
        self.logger.info('Enqueued: %s' % qres)

    def mainloop(self):
        if self.seed_urls:
            self.init_db()
            self.seed_queue(self.seed_urls)

        while True:
            try:
                msg = self.fetch_results.get_nowait()
                self.store_new_url(msg)
            except Empty:
                pass

            if self.fetch_queue.qsize() < self.fetch_queue_preload:
                for _ in xrange(self.fetch_queue_preload):
                    qres = self.dequeue_next_qres()
                    if qres:
                        msg = {
                            'qres': qres,
                            'keep_tempfile': True,
                        }
                        self.fetch_queue.put(msg)
            else:
                time.sleep(0.01)
