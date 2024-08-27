import logging

def cadaid_logger(name: str) -> logging.Logger:
    """Set up a logger with the given name."""
    
    logger = logging.getLogger(name)
  
    if not logger.handlers:  
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger