import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FILENAME = Path.cwd() / "logs" / "live_adclicker.log"
LOG_FILENAME.parent.mkdir(exist_ok=True)

# Create a custom logger
live_logger = logging.getLogger(__name__)
live_logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(
    LOG_FILENAME, maxBytes=20971520, encoding="utf-8", backupCount=50
)
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
console_log_format = "%(asctime)s [%(levelname)5s] %(lineno)3d: %(message)s"
file_log_format = "%(asctime)s [%(levelname)5s] %(filename)s:%(lineno)3d: %(message)s"
console_formatter = logging.Formatter(console_log_format, datefmt="%d-%m-%Y %H:%M:%S")
console_handler.setFormatter(console_formatter)
file_formatter = logging.Formatter(file_log_format, datefmt="%d-%m-%Y %H:%M:%S")
file_handler.setFormatter(file_formatter)

# Add handlers to the logger
live_logger.addHandler(console_handler)
live_logger.addHandler(file_handler)


class MultiprocessLogFilter(logging.Filter):
    """Custom log filter for multiple browser runs

    :type browser_id: str
    :param browser_id: Id for browser instance
    """

    def __init__(self, browser_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.browser_id = browser_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Register custom keyword for log formatters

        :type record: logging.LogRecord
        :param record: LogRecord instance
        :rtype: bool
        :returns: True
        """

        record.browser_id = self.browser_id

        return True


def live_update_log_formats(browser_id: str) -> None:
    """Update log formats for multiprocess runs

    :type browser_id: str
    :param browser_id: Id for browser instance
    """

    live_logger.removeHandler(console_handler)
    live_logger.removeHandler(file_handler)

    console_log_format = "%(asctime)s <<%(browser_id)s>> [%(levelname)5s] %(lineno)3d: %(message)s"
    file_log_format = (
        "%(asctime)s <<%(browser_id)s>> [%(levelname)5s] %(filename)s:%(lineno)3d: %(message)s"
    )
    console_formatter = logging.Formatter(console_log_format, datefmt="%d-%m-%Y %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    file_formatter = logging.Formatter(file_log_format, datefmt="%d-%m-%Y %H:%M:%S")
    file_handler.setFormatter(file_formatter)

    console_handler.addFilter(MultiprocessLogFilter(browser_id))
    file_handler.addFilter(MultiprocessLogFilter(browser_id))

    live_logger.addHandler(console_handler)
    live_logger.addHandler(file_handler)
