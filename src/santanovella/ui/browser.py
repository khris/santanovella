import json
import logging
import tkinter
from collections.abc import Iterable
from copy import copy
from dataclasses import astuple, dataclass

from .. import html
from ..protocol.common import Response, Url

MAX_REDIRECTION = 2
WIDTH = 800
HEIGHT = 600
SCROLL_STEP = 100


@dataclass
class Vec2:
    x: float
    y: float


@dataclass
class Char:
    pos: Vec2
    char: str


class Browser:
    display_list: Iterable[Char]

    def __init__(self):
        self.window = tkinter.Tk()
        self.window.bind('<Down>', lambda e: self.do_scroll(e, SCROLL_STEP))
        self.window.bind('<Up>', lambda e: self.do_scroll(e, -SCROLL_STEP))
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack()
        self.display_list = []
        self.scroll = 0

    def show_content_from(self, url: Url):
        curr_url = url
        body = ''
        for _ in range(MAX_REDIRECTION + 1):
            res: Response = curr_url.request()
            print('# Response')
            print('## Header')
            res.headers.show()
            print('## Body')
            if res.content_type.type == 'text':
                if res.content_type.subtype == 'html':
                    body = html.lex(res.text)
                else:
                    body = res.text
            elif res.content_type.type == 'application':
                if res.content_type.subtype == 'json':
                    body = json.dumps(res.json, indent=2)

            if not res.should_redirect:
                break

            curr_url = Url.create_from(res.redirect_path)
        else:
            logging.warning('redirected %d times, stopped' % MAX_REDIRECTION)

        self.display_list = self.layout(body)
        self.draw()

    def draw(self):
        for char in self.display_list:
            self.canvas.create_text(char.pos.x, char.pos.y - self.scroll, text=char.char)

    def do_scroll(self, e, step):
        self.scroll += step
        self.canvas.delete('all')
        self.draw()

    @staticmethod
    def layout(text) -> Iterable[Char]:
        display_list = []
        step = Vec2(13.0, 18.0)
        cursor = Vec2(*astuple(step))
        for c in text:
            if cursor.x >= WIDTH - step.x or c == '\n':
                cursor.x = step.x
                cursor.y += step.y
            display_list.append(Char(copy(cursor), c))
            cursor.x += step.x
        return display_list
