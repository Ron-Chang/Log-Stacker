import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class Dyer:

    _RESETALL = '\x1b[0m'
    _STYLE = '\x1b[{style}'
    _FG = '3{fg}'
    _BG = '4{bg}'

    class Style:
        NORMAL = 0
        BOLD = 1
        DARK = 2
        ITALIC = 3
        UNDERSCORE = 4
        BLINK = 5
        UNKNOWN = 6
        TURNOVER = 7
        STRIKE_THROUGH = 9
        HIDE = 8

    class Color:
        BLACK = 0
        RED = 1
        GREEN = 2
        YELLOW = 3
        BLUE = 4
        PURPLE = 5
        CYAN = 6
        GRAY = 7

    @classmethod
    def _validate(cls, fg, bg):
        if fg is None and bg is None:
            raise ValueError('fg and bg either one of them is required.')
        if fg not in cls.Color.__dict__.values():
            raise ValueError('fg color code is out of range.')
        if bg not in cls.Color.__dict__.values():
            raise ValueError('bg color code is out of range.')

    @classmethod
    def dye(cls, fg=None, bg=None, style=None):
        cls._validate(fg=fg, bg=bg)
        style_tag = f'\x1b[{cls.Style.NORMAL};' if style is None else f'\x1b[{style};'
        fg_tag = f'30' if fg is None else f'3{fg}'
        bg_tag = '' if bg is None else f';4{bg}'
        return f'{style_tag}{fg_tag}{bg_tag}m'

    @classmethod
    def reset(cls):
        return cls._RESETALL


class LoggerFormatter(logging.Formatter):

    LOGGING_STYLE = logging.PercentStyle

    STREAM = 1
    FILE = 2

    _RESET = Dyer.reset()

    _FG_CYAN = Dyer.dye(fg=Dyer.Color.CYAN)
    _BG_CYAN = Dyer.dye(bg=Dyer.Color.CYAN)

    _FG_GREEN = Dyer.dye(fg=Dyer.Color.GREEN)
    _BG_GREEN = Dyer.dye(bg=Dyer.Color.GREEN)

    _FG_YELLOW = Dyer.dye(fg=Dyer.Color.YELLOW)
    _BG_YELLOW = Dyer.dye(bg=Dyer.Color.YELLOW)

    _FG_PURPLE = Dyer.dye(fg=Dyer.Color.PURPLE)
    _BG_PURPLE = Dyer.dye(bg=Dyer.Color.PURPLE)

    _FG_RED_HIGHLIGHT = Dyer.dye(fg=Dyer.Color.RED, style=Dyer.Style.BOLD)
    _BG_RED_HIGHLIGHT = Dyer.dye(bg=Dyer.Color.RED, style=Dyer.Style.BLINK)

    _STREAM_FMT = '[%(asctime)s] {badge_color}[%(levelname)-8s]{reset} {text_color}[%(message)s]{reset}'
    _DEFAULT_FMT = '[%(asctime)s] [%(levelname)-10s] [%(message)s]'

    _STREAM_INFO_FORMAT = _STREAM_FMT.format(
        badge_color=_BG_GREEN,
        text_color=_FG_GREEN,
        reset=_RESET
    )
    _STREAM_DEBUG_FORMAT = _STREAM_FMT.format(
        badge_color=_BG_CYAN,
        text_color=_FG_CYAN,
        reset=_RESET
    )
    _STREAM_WARNING_FORMAT = _STREAM_FMT.format(
        badge_color=_BG_YELLOW,
        text_color=_FG_YELLOW,
        reset=_RESET
    )
    _STREAM_ERROR_FORMAT = _STREAM_FMT.format(
        badge_color=_BG_PURPLE,
        text_color=_FG_PURPLE,
        reset=_RESET
    )
    _STREAM_CRITICAL_FORMAT = _STREAM_FMT.format(
        badge_color=_BG_RED_HIGHLIGHT,
        text_color=_FG_RED_HIGHLIGHT,
        reset=_RESET
    )

    _STREAM_FORMATS = {
        logging.INFO: LOGGING_STYLE(_STREAM_INFO_FORMAT),
        logging.DEBUG: LOGGING_STYLE(_STREAM_DEBUG_FORMAT),
        logging.WARNING: LOGGING_STYLE(_STREAM_WARNING_FORMAT),
        logging.ERROR: LOGGING_STYLE(_STREAM_ERROR_FORMAT),
        logging.CRITICAL: LOGGING_STYLE(_STREAM_CRITICAL_FORMAT),
    }

    _FILE_FORMATS = {
        logging.INFO: LOGGING_STYLE(_DEFAULT_FMT),
        logging.DEBUG: LOGGING_STYLE(_DEFAULT_FMT),
        logging.WARNING: LOGGING_STYLE(_DEFAULT_FMT),
        logging.ERROR: LOGGING_STYLE(_DEFAULT_FMT),
        logging.CRITICAL: LOGGING_STYLE(_DEFAULT_FMT),
    }

    def __init__(self, type_, fmt=None):
        """
        Cannot recognized by instance() method
        logging.FileHandler is inherit from logging.StreamHandler
        """
        fmt = fmt or self._DEFAULT_FMT
        super().__init__(fmt=fmt)
        self.type_ = type_

    def format(self, record):
        self._style = self.LOGGING_STYLE(self._DEFAULT_FMT)
        if self.type_ == self.STREAM:
            self._style = self._STREAM_FORMATS.get(record.levelno, self._style)
        elif self.type_ == self.FILE:
            self._style = self._FILE_FORMATS.get(record.levelno, self._style)
        return logging.Formatter.format(self, record)


class StreamLogger:

    def get_handler(level=logging.DEBUG):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = LoggerFormatter(type_=LoggerFormatter.STREAM)
        handler.setFormatter(formatter)
        return handler


class FileLogger:

    _TITLE = os.environ.get('APP_NAME', 'default_log').replace(' ', '_').lower()
    _ROOT = os.path.abspath('.')

    _LEVEL_MAPS = {
        logging.DEBUG: 'debug',
        logging.INFO: 'info',
        logging.WARNING: 'warning',
        logging.ERROR: 'error',
        logging.CRITICAL: 'critical',
    }

    @staticmethod
    def _get_rotating_file_handler(filename, level=logging.DEBUG):
        handler = TimedRotatingFileHandler(
            filename=filename,
            when='H',
            interval=1,
            backupCount=10000,
            encoding=None,
            delay=False,
            utc=False,
        )
        handler.setLevel(level)
        formatter = LoggerFormatter(type_=LoggerFormatter.FILE)
        handler.setFormatter(formatter)
        return handler

    @classmethod
    def get_handlers(cls, entry_point, level=logging.DEBUG):
        handlers = list()
        for levelno, level_name in cls._LEVEL_MAPS.items():
            if levelno < level:
                continue
            path = f'{cls._ROOT}/log/{level_name}_log'
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(f'{path}/{cls._TITLE}.{entry_point}.{level_name}.log')
            handler = cls._get_rotating_file_handler(filename=filename, level=levelno)
            handlers.append(handler)
        return handlers


class LogStacker:
    """
    - How to use:

        Import LogStacker at the entry point and customized optional settings before LogStacker.logging(__file__)

        from log_stacker import LogStacker

        # -------------- optional settings start -------------- #
        LogStacker.STREAM_OUTPUT = True
        # default: True
        LogStacker.LOCAL_OUTPUT = True
        # default: True

        LogStacker.ROOT_LEVEL = LogStacker.DEBUG
        # default: LogStacker.DEBUG
        LogStacker.STREAM_LEVEL = LogStacker.WARNING
        # default: LogStacker.DEBUG
        LogStacker.LOCAL_LEVEL = LogStacker.DEBUG
        # default: LogStacker.DEBUG

        LogStacker.TRACEBACK_LEVEL.add(LogStacker.INFO)
        # default: {LogStacker.WARNING, LogStacker.ERROR, LogStacker.CRITICAL}

        LogStacker.IGNORE_PACKAGES.add('package_name_str')
        # default: {}

        # In progress attributes
        # LogStacker.REMOTE_OUTPUT = False
        # LogStacker.REMOTE_LEVEL = LogStacker.DEBUG

        # -------------- optional settings end -------------- #

        LogStacker.logging(__file__)
    """

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    ROOT_LOGGER = None

    STREAM_OUTPUT = True
    LOCAL_OUTPUT = True

    ROOT_LEVEL = logging.DEBUG
    STREAM_LEVEL = logging.DEBUG
    FILE_LEVEL = logging.DEBUG

    # REMOTE_OUTPUT = True  # in progress
    # REMOTE_LEVEL = logging.DEBUG  # in progress

    TRACEBACK_LEVEL = {
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    }

    IGNORE_PACKAGES = {}

    @classmethod
    def _update_root_logger(cls, handlers):
        cls.ROOT_LOGGER = logging.getLogger()
        cls.ROOT_LOGGER.setLevel(cls.ROOT_LEVEL)
        for handler in handlers:
            cls.ROOT_LOGGER.addHandler(handler)

    @staticmethod
    def _resist_packages(packages):
        for package in packages:
            logging.getLogger(package).setLevel(logging.WARNING)
        logging.captureWarnings(True)

    @classmethod
    def logging(cls, entry_point, stream_level=None, file_level=None, remote_level=None):
        """
        TODO
            if cls.REMOTE_OUTPUT:
                add fluent
        """
        entry_point = os.path.basename(entry_point)
        handlers = list()
        if cls.STREAM_OUTPUT:
            stream_handler = StreamLogger.get_handler(level=cls.STREAM_LEVEL)
            handlers.append(stream_handler)
        if cls.LOCAL_OUTPUT:
            file_handlers = FileLogger.get_handlers(entry_point=entry_point, level=cls.FILE_LEVEL)
            handlers.extend(file_handlers)

        cls._update_root_logger(handlers=handlers)
        cls._resist_packages(packages=cls.IGNORE_PACKAGES)

    @classmethod
    def _validate(cls):
        if cls.ROOT_LOGGER is None:
            raise Exception(f'LogStacker Error: Initialization is required. \n{cls.__doc__}')

    @classmethod
    def _get_traceback(cls, level):
        if level not in cls.TRACEBACK_LEVEL:
            return str()
        result = traceback.format_exc()
        if 'NoneType: None' in result:
            return str()
        return result

    @classmethod
    def _get_msg(cls, level, msg=None, exception=None):
        message = msg or str()
        exception = exception or str()
        exception_traceback = cls._get_traceback(level=level)
        output = (
            f'\n\t<MESSAGE>: {message}'
            f'\n\t<EXCEPTION>: {exception}'
            f'\n\t<TRACEBACK>: \n{exception_traceback}'
        )
        return output

    @classmethod
    def debug(cls, exception=None, msg=None):
        cls._validate()
        msg = cls._get_msg(level=logging.DEBUG, msg=msg, exception=exception)
        cls.ROOT_LOGGER.debug(msg=msg)

    @classmethod
    def info(cls, exception=None, msg=None):
        cls._validate()
        msg = cls._get_msg(level=logging.INFO, msg=msg, exception=exception)
        cls.ROOT_LOGGER.info(msg=msg)

    @classmethod
    def warning(cls, exception=None, msg=None):
        cls._validate()
        msg = cls._get_msg(level=logging.WARNING, msg=msg, exception=exception)
        cls.ROOT_LOGGER.warning(msg=msg)

    @classmethod
    def error(cls, exception=None, msg=None):
        cls._validate()
        msg = cls._get_msg(level=logging.ERROR, msg=msg, exception=exception)
        cls.ROOT_LOGGER.error(msg=msg)

    @classmethod
    def critical(cls, exception=None, msg=None):
        cls._validate()
        msg = cls._get_msg(level=logging.CRITICAL, msg=msg, exception=exception)
        cls.ROOT_LOGGER.critical(msg=msg)

