import logging
from market_maker.settings import settings


def setup_custom_logger(name, log_level=settings.LOG_LEVEL):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    logger = logging.getLogger(name)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
 #   logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return logger
