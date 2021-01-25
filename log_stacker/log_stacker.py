import logging
import traceback
from datetime import datetime


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

    _STREAM_FMT =  '[%(asctime)s] {badge_color}[%(levelname)-10s]{reset}{text_color}%(message)s{reset}'
    _DEFAULT_FMT =  '[%(asctime)s] [%(levelname)-10s] %(message)s'

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

    def __init__(self, type_):
        """
        Cannot recognized by instance() method
        logging.FileHandler is inherit from logging.StreamHandler
        """
        super().__init__()
        self.type_ = type_

    def format(self, record):
        self._style = self.LOGGING_STYLE(self._DEFAULT_FMT)
        if self.type_ == self.STREAM:
            self._style = self._STREAM_FORMATS.get(record.levelno, self._style)
        elif self.type_ == self.FILE:
            self._style = self._FILE_FORMATS.get(record.levelno, self._style)
        return logging.Formatter.format(self, record)


class LogStacker:

    _DEFAULT_STREAM_LEVEL = logging.DEBUG
    _DEFAULT_FILE_LEVEL = logging.DEBUG

    _TRACEBACK_LEVEL = {
        logging.ERROR,
        logging.CRITICAL
    }

    def __init__(self, path, trap_level=None, stream_level=None, file_level=None):
        self.path = path
        self.stream_level = stream_level
        self.file_level = file_level

        # 實例化logger 物件
        self.logger = logging.getLogger(path)
        # 設定 logger 捕捉層級
        self.logger.setLevel(trap_level or logging.DEBUG)

        self._add_stream_handler()
        self._add_file_handler()

    def _add_stream_handler(self):
        # 建立 輸出處理器 顯示訊息
        stream_handler = logging.StreamHandler()
        # 設定 輸出處理器 捕捉層級
        stream_handler.setLevel(self.stream_level or self._DEFAULT_STREAM_LEVEL)
        # 設定 輸出處理器 格式
        stream_handler.setFormatter(
            LoggerFormatter(type_=LoggerFormatter.STREAM)
        )
        # 將 輸出處理器 加入logger
        self.logger.addHandler(stream_handler)

    def _add_file_handler(self):
        # 建立 日誌處理器 記錄訊息
        file_handler = logging.FileHandler(f'{datetime.now().strftime("%F")}-{self.path}.log')
        # 設定 日誌處理器 捕捉層級
        file_handler.setLevel(self.file_level or self._DEFAULT_FILE_LEVEL)
        # 設定 日誌處理器 格式
        file_handler.setFormatter(
            LoggerFormatter(type_=LoggerFormatter.FILE)
        )
        # 將 日誌處理器 加入logger
        self.logger.addHandler(file_handler)

    @classmethod
    def _get_traceback(cls, level):
        traceback_ = traceback.format_exc()
        if level in cls._TRACEBACK_LEVEL and 'NoneType: None' not in traceback_:
            return traceback_
        return str()

    @classmethod
    def _get_msg(cls, level, msg=None, exception=None):
        message = msg or str()
        exception = exception or str()
        traceback_ = cls._get_traceback(level=level)
        output = (
            f'\n\t<MESSAGE>: {message}'
            f'\n\t<EXCEPTION>: {exception}'
            f'\n\t<TRACEBACK>: \n{traceback_}'
        )
        return output

    def debug(self, exception=None, msg=None):
        msg = self._get_msg(level=logging.DEBUG, msg=msg, exception=exception)
        self.logger.debug(msg=msg)

    def info(self, exception=None, msg=None):
        msg = self._get_msg(level=logging.INFO, msg=msg, exception=exception)
        self.logger.info(msg=msg)

    def warning(self, exception=None, msg=None):
        msg = self._get_msg(level=logging.WARNING, msg=msg, exception=exception)
        self.logger.warning(msg=msg)

    def error(self, exception=None, msg=None):
        msg = self._get_msg(level=logging.ERROR, msg=msg, exception=exception)
        self.logger.error(msg=msg)

    def critical(self, exception=None, msg=None):
        msg = self._get_msg(level=logging.CRITICAL, msg=msg, exception=exception)
        self.logger.critical(msg=msg)

