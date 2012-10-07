import logging

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    return logger
