import logging

from .ui.browser import Browser

logging.basicConfig(level=logging.DEBUG)

import tkinter
import sys

from .protocol.common import Url


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: santanovella <url>')
        exit(1)

    url = Url.create_from(sys.argv[1])
    browser = Browser()
    browser.show_content_from(url)
    tkinter.mainloop()
