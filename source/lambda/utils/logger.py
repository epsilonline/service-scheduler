import logging
from configuration import logging_level

fmt = '[%(levelname)s] %(name)s: %(message)s'
logging.basicConfig(format=fmt)

# Disable boto logger
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)


def get_logger(logger_name: str, log_level: str = logging_level):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    return logger
