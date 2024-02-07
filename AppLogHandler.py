# app-based log handling, see https://github.com/Textualize/textual/discussions/2072
from textual.widgets import RichLog

import logging


class AppLogHandler(logging.Handler):
    """Class for logging to a textual widget"""
    
    # TODO: Subclass RichLog to be a formal widget, handle on_ready here.

    def __init__(self, log_widget:RichLog):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.write(msg)