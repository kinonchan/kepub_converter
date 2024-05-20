import logging
import configparser

class Kepub_converter_logger:

    def __init__(self, config):
        self.log_level = logging.INFO  #Default value
        self.config = config
        self.log = logging.getLogger("kepub_converter")

        # Get the logging level from the INI file
        self.log_level_str = self.config.get('LOGGING', 'logLevel', fallback='INFO').upper()
        self.log_format = self.config['LOGGING']['logFormat']

        # Define a dictionary to map the logging level from string to the actual logging level
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        # Get the corresponding logging level object
        self.log_level = self.log_levels.get(self.log_level_str, logging.INFO)

        # Configure logging with the level from the INI file
        logging.basicConfig(level=self.log_level, format=self.log_format)
    
    def info(self, string):
        self.log.info(string)

    def warn(self, string):
        self.log.warn(string)

    def error(self, string):
        self.log.error(string)

    def debug(self, string):
        self.log.debug(string)