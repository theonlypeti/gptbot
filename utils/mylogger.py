import logging
from logging.handlers import WatchedFileHandler
from datetime import datetime
from os import makedirs
import coloredlogs

baselogger = logging.getLogger("main")
logging.addLevelName(25, "Event")

#formatting the colorlogger
fmt = "[ %(asctime)s %(name)s (%(filename)s) %(lineno)d %(funcName)s() %(levelname)s ] %(message)s"
coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'lineno': {'color': 'magenta'}, 'levelname': {'bold': True, 'color': 'black'}, 'filename': {'color': 25}, 'name': {'color': 'blue'}, 'funcname': {'color': 'cyan'}}
coloredlogs.DEFAULT_LEVEL_STYLES = {'critical': {'bold': True, 'color': 'red'}, 'debug': {'bold': True, 'color': 'black'}, 'error': {'color': 'red'}, 'info': {'color': 'green'}, 'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True}, 'success': {'bold': True, 'color': 'green'}, 'verbose': {'color': 'blue'}, 'warning': {'color': 'yellow'}, "Event": {"color": "white"}}


def init(args=None):
    if args and args.logfile: #if you need a text file
        FORMAT = "[{asctime}][{name}][{filename}][{lineno:4}][{funcName}][{levelname}] {message}"
        formatter = logging.Formatter(FORMAT, style="{")  # this is for default logger
        filename = f"./logs/bot_log_{datetime.now().strftime('%m-%d-%H-%M-%S')}.txt"
        makedirs(r"./logs", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as _:
            pass
        fl = WatchedFileHandler(filename, encoding="utf-8") #not for windows but if i ever switch to linux
        fl.setFormatter(formatter)
        fl.setLevel(logging.DEBUG)
        fl.addFilter(lambda rec: rec.levelno == 25)
        baselogger.addHandler(fl)

    baselogger.setLevel(logging.DEBUG)  # base is debug, so the file handler could catch debug msgs too
    if args and args.debug:
        coloredlogs.install(level=logging.DEBUG, logger=baselogger, fmt=fmt)
    else:
        coloredlogs.install(level=logging.INFO, logger=baselogger, fmt=fmt)
    return baselogger
