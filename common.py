import logging
import sys


def get_logger():
    logging.basicConfig(stream=sys.stdout, format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)d|%(message)s")
    logger = logging.getLogger()
    logger.setLevel('INFO')

    return logger
