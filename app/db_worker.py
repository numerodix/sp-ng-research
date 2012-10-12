import os
import time

from app import db
from models import QueuedUrl

from workerbase import Worker


class DbWorker(Worker):
    def __init__(self, fetch_queue, fetch_results, seed_url=None):
        # init multiproc data structures
        self.fetch_queue = fetch_queue
        self.fetch_results = fetch_results
        self.seed_url = seed_url

        # call base, dispatches to .mainloop
        super(DbWorker, self).__init__()

    def init_db(self):
        self.logger.info('Preparing datastore')

        os.system('sudo /etc/init.d/postgresql restart')
        os.system('dropdb crawl')
        os.system('createdb crawl')

        self.logger.info('Creating models')
        db.create_all()

    def seed_db(self, url):
        qurl = QueuedUrl(
            url=url,
            level=0,
            #context='',
            #parent_url='',
        )
        db.session.add(qurl)
        db.session.commit()

    def dequeue_next(self):
        qurl = QueuedUrl.query.filter(
            QueuedUrl.processing_status == 'new',
        ).first()
        if qurl:
            self.logger.debug('Dequeued: %s' % qurl)
            QueuedUrl.query.filter(QueuedUrl.id == qurl.id).delete()
            db.session.commit()
            return qurl

    def mainloop(self):
        if self.seed_url:
            self.init_db()
            self.seed_db(self.seed_url)

        while True:
            if self.fetch_queue.qsize() < 1:
                qurl = self.dequeue_next()
                self.fetch_queue.put(qurl)
            else:
                time.sleep(0.1)
