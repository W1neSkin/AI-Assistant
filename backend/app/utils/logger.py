import logging
import sys
from pathlib import Path

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

def setup_debug_logger():
    logger = logging.getLogger("debugger")
    logger.setLevel(logging.DEBUG)
    
    # Console handler with detailed format
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(ch)
    
    # File handler for persistent logs
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(log_dir / "debug.log")
    logger.addHandler(fh)
    
    return logger 