import json
import logging
import tkinter
from collections.abc import Iterable
from copy import copy
from dataclasses import astuple, dataclass
from tkinter import Event, EventType

from .. import html
from ..protocol.common import Response, Url

MAX_REDIRECTION = 2
SCROLL_STEP = 100
DIV_GAP = 27


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
        self.window.bind('<MouseWheel>', lambda e: self.do_scroll(e, SCROLL_STEP))
        self.canvas = tkinter.Canvas(self.window)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.on_resize(e))
        self.display_list = []
        self.scroll = 0
        self.body = ''
        self.width = 0
        self.height = 0

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

        self.body = body
        self.display_list = self.layout()
        self.draw()

    def draw(self):
        for char in self.display_list:
            scrolled_pos = Vec2(char.pos.x, char.pos.y - self.scroll)
            if not is_in(0, 0, self.width, self.height, scrolled_pos):
                continue
            self.canvas.create_text(astuple(scrolled_pos), text=char.char)

    def do_scroll(self, e: Event, step):
        match e.type:
            case EventType.MouseWheel:
                self.scroll += e.delta * step * 0.1
            case EventType.KeyPress:
                self.scroll += step
            case _:
                return
        logging.debug('scroll %d' % self.scroll)
        self.canvas.delete('all')
        self.draw()

    def on_resize(self, e: Event):
        logging.debug('resize %s: %d * %d' % (e.widget, e.width, e.height))
        self.width, self.height = e.width, e.height
        self.layout()
        self.draw()

    def layout(self) -> Iterable[Char]:
        display_list = []
        step = Vec2(13.0, 18.0)
        cursor = Vec2(*astuple(step))
        for c in self.body:
            if cursor.x >= self.width:
                cursor.x = step.x
                cursor.y += step.y
            elif c == '\n':
                cursor.x = step.x
                cursor.y += step.y + DIV_GAP

            display_list.append(Char(copy(cursor), c))
            cursor.x += step.x
        return display_list


def is_in(x, y, width, height, pos: Vec2) -> bool:
    return x <= pos.x <= x + width and y <= pos.y <= y + height


def has_attr(obj, attr):
    attr = getattr(obj, attr, None)
    return attr is not None
