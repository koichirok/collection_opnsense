import logging
import sys
import ndebug

# Set the default logging level to CRITICAL
logger = logging.getLogger("module_generator")
logger.setLevel(logging.CRITICAL)

def log(*args, **kwargs):
    if logger.level <= logging.CRITICAL:
        print(*args, **kwargs)

def warning(*args, **kwargs):
    print("WARN:", *args, file=sys.stderr, **kwargs)

def critical(*args, **kwargs):
    print("CRITICAL:", *args, file=sys.stderr, **kwargs)

def log_v(*args, **kwargs):
    logger.error(*args, **kwargs)


def log_vv(*args, **kwargs):
    logger.warning(*args, **kwargs)


def log_vvv(*args, **kwargs):
    logger.info(*args, **kwargs)


def log_d(*args, **kwargs):
    logger.debug(*args, **kwargs)


class Base:
    _debug = None

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        if self.__class__._debug is None:
            self.__class__._debug = ndebug.create(f"{self.__module__}.{self.__class__.__qualname__}")

    def debug(self, *args, **kwargs):
        self._debug(*args, **kwargs)  # pylint: disable=not-callable

