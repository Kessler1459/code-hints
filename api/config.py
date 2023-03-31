import logging
import os

logging_level = os.getenv('LOGGING', 'INFO')

def set_logger():
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    logging.basicConfig(
        level=levels.get(logging_level) or logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)8s --> %(message)s",
        datefmt="%Y-%m-%d  %H:%M:%S",
    )
    for library in ('boto3', 'botocore', 'urllib3'):
        logging.getLogger(library).setLevel(logging.ERROR)
