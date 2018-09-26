import warnings
import functools
import logging
import json
import copy
from logging import config as logconf

WEB = 400
MAIL = 500
ADDRESS = 'yourbotnamehere@gmail.com'
TOADRESSES = ['to1@foo.com', 'to2@foo.com']
PW = 'yourbotapppassword'
logging.addLevelName(WEB, 'WEB')
logging.addLevelName(MAIL, 'MAIL')

LOG_CONF = {
    "version": 1,
    'disable_existing_loggers': True,
    "formatters": {
        "verbose": {
            "format":
            "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {
            "format": "%(levelname)s %(message)s"
        },
        "fixedwidth": {
            "()": "tools.misc.ColorFormatter",
            "format":
            "[[p]%(asctime)s %(name)-25s[/]] %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "filters": {
        "streamlimitfilter": {
            "()": "tools.misc.LimitFilter",
            "level": (0, WEB - 1)
        },
        "weblimitfilter": {
            "()": "tools.misc.LimitFilter",
            "level": (WEB, MAIL - 1)
        },
        "maillimitfilter": {
            "()": "tools.misc.LimitFilter",
            "level": (MAIL, MAIL + 1)
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "fixedwidth",
            "filters": ["streamlimitfilter", ]
        },
        "webhandler": {
            "level": 9000,
            "class": "tools.misc.HTTPJSONHandler",
            "host": "152.66.244.231",
            "url": "/log/compnet.php",
            "method": "POST",
            "filters": ["weblimitfilter", ]
        },
        "mailhandler": {
            "level": 9000,
            "class": "logging.handlers.SMTPHandler",
            "mailhost": ("smtp.gmail.com", 587),
            "fromaddr": ADDRESS,
            "toaddrs": TOADRESSES,
            "subject": "compnet logs",
            "credentials": (ADDRESS, PW),
            "filters": ["maillimitfilter", ],
            "secure": ()
        }
    },
    "loggers": {
        "compnet": {
            "handlers": ["console", "webhandler", "mailhandler"],
            "propagate": False,
            "level": "DEBUG"
        }
    }
}


class LimitFilter(logging.Filter):
    def __init__(self, level):
        if isinstance(level, tuple):
            self.minlevel, self.maxlevel = level
        else:
            self.minlevel = level
            self.maxlevel = level

    def filter(self, record):
        if record.levelno < self.minlevel or record.levelno > self.maxlevel:
            return False
        return True


class ColorFormatter(logging.Formatter):
    bold = '[bb]'
    italic = '[i]'
    underline = '[_]'
    invert = '[\]'
    crossed = '[-]'
    red = '[r]'
    green = '[g]'
    yellow = '[y]'
    blue = '[b]'
    purple = '[p]'
    sky = '[s]'
    grey = '[grey]'
    red_bg = '[r_bg]'
    green_bg = '[g_bg]'
    yellow_bg = '[y_bg]'
    blue_bg = '[b_bg]'
    purple_bg = '[p_bg]'
    sky_bg = '[s_bg]'
    grey_bg = '[grey_bg]'

    emph_ = '[/]'

    colors = {
        bold: '\033[1;1m',
        italic: '\033[1;3m',
        underline: '\033[1;4m',
        invert: '\033[1;7m',
        crossed: '\033[1;9m',
        red: '\033[1;31m',
        green: '\033[1;32m',
        yellow: '\033[1;33m',
        blue: '\033[1;34m',
        purple: '\033[1;35m',
        sky: '\033[1;36m',
        grey: '\033[1;37m',
        red_bg: '\033[1;41m',
        green_bg: '\033[1;42m',
        yellow_bg: '\033[1;43m',
        blue_bg: '\033[1;44m',
        purple_bg: '\033[1;45m',
        sky_bg: '\033[1;46m',
        grey_bg: '\033[1;47m',
        emph_: '\033[0m'
    }

    def __init__(self, format, *args, **kwargs):
        for k, color in self.colors.iteritems():
            format = format.replace(k, color)

        super(ColorFormatter, self).__init__(format, *args, **kwargs)

    def format(self, record):
        record = copy.copy(record)
        for k, color in self.colors.iteritems():
            record.msg = record.msg.replace(k, color)

        return super(ColorFormatter, self).format(record)


class HTTPJSONHandler(logging.handlers.HTTPHandler):
    def mapLogRecord(self, record):
        params = json.loads(record.msg)
        return params


def logger_setup(conf=None):
    if conf is None:
        conf = LOG_CONF
    logconf.dictConfig(conf)
    # logging.getLogger('compnet').setLevel(logging.INFO)


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1)
        return func(*args, **kwargs)

    return new_func
