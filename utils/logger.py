import logging
import os

def cadaid_logger(name: str) -> logging.Logger:
    """Set up a logger with the given name."""
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Create a file handler
        log_file = '/app/logs/app.log'
        file_handler = logging.FileHandler(log_file, mode='a')  # Changed to 'a' for append mode
        file_handler.setLevel(logging.DEBUG)
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create a formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Add a session separator to the log file
        with open(log_file, 'a') as f:
            f.write('\n' + '='*50 + '\n')
            f.write('New Session Started\n')
            f.write('='*50 + '\n\n')

    return logger