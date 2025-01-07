import logging
from datetime import datetime
import os

class ErrorLogger:
    def __init__(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up logging configuration
        self.logger = logging.getLogger('database_operations')
        self.logger.setLevel(logging.ERROR)
        
        # Create a file handler
        log_file = f'logs/error_log_{datetime.now().strftime("%Y%m%d")}.log'
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.ERROR)
        
        # Create a formatting for the logs
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add the handler to the logger
        self.logger.addHandler(handler)
    
    def log_error(self, operation, error, details=None):
        """
        Log an error with operation context and details.
        
        Args:
            operation (str): The operation being performed when error occurred
            error (Exception): The error that occurred
            details (dict, optional): Additional details about the operation
        """
        error_msg = f"Operation: {operation}\nError: {str(error)}"
        if details:
            error_msg += f"\nDetails: {details}"
        self.logger.error(error_msg) 