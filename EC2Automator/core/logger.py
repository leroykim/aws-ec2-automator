# core/logger.py

"""
logger.py
=========

Configures and provides a logger for the EC2 Automator application.

This module sets up logging by creating a dedicated logs directory, defining a log file
with a timestamp, and configuring the logging settings to output logs to both a file
and the console. It initializes a logger instance that can be used throughout the application
for consistent and centralized logging of events, errors, and informational messages.

Attributes
----------
LOG_DIR : str
    The directory path where log files are stored.
log_filename : str
    The name of the current log file, including a timestamp.
log_filepath : str
    The full file path to the current log file.
logger : logging.Logger
    The configured logger instance used for logging messages.

Usage
-----
To use the logger in other modules, import the `logger` instance:
    
    from core.logger import logger

    logger.info("This is an informational message.")
    logger.error("This is an error message.")

"""

import logging
import os
from datetime import datetime

# Create a logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file name with timestamp
log_filename = datetime.now().strftime("ec2_automator_%Y%m%d_%H%M%S.log")
log_filepath = os.path.join(LOG_DIR, log_filename)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filepath), logging.StreamHandler()],
)

# Initialize the logger
logger = logging.getLogger(__name__)
logger.debug(f"Logger '{logger.name}' initialized.")
