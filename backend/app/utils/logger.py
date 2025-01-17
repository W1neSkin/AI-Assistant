import logging
import sys

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create console handler with a more visible format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create a more detailed formatter
    formatter = logging.Formatter(
        '\n%(asctime)s - %(name)s - %(levelname)s'
        '\n>>> %(message)s'
        '\n-------------------------------------------'
    )
    console_handler.setFormatter(formatter)

    # Remove any existing handlers and add our new one
    logger.handlers = []
    logger.addHandler(console_handler)

    return logger 