import logging


formatter = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-6s %(message)s')

class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        s = formatter.format(record)
        header, footer = s.split(record.msg)
        s = s.replace('\n', '\n' + ' '*len(header))
        return s

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(MultiLineFormatter())

    logger.addHandler(stream_handler)

    return logger
