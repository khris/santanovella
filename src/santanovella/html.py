import json
from enum import auto, Enum
from pathlib import Path

entity_data = Path(__file__).parent.joinpath('entities.json')
with open(entity_data, 'r') as f:
    RESERVED_ENTITIES = json.load(f)
    LAST_CHARS_NO_CLOSING = tuple(k[-1] for k, v in RESERVED_ENTITIES.items()
                                  if not k.endswith(';'))


class HtmlParserState(Enum):
    Default = auto()
    Tag = auto()
    Entity = auto()
    Skip1Char = auto()


def show(body: str):
    state_stack = [HtmlParserState.Default]
    tag_buf = []
    entity_buf = []

    for i, c in enumerate(body):
        if state_stack[-1] == HtmlParserState.Default:
            if c == '<':
                state_stack.append(HtmlParserState.Tag)
            elif c == '&':
                state_stack.append(HtmlParserState.Entity)
                entity_buf.append(c)
            else:
                print(c, end='')
        elif state_stack[-1] == HtmlParserState.Tag:
            if c == '>':
                tag_buf.clear()
                state_stack.pop()
            else:
                tag_buf.append(c)
        elif state_stack[-1] == HtmlParserState.Entity:
            entity_buf.append(c)
            if c == ';':
                print(RESERVED_ENTITIES[''.join(entity_buf)]['characters'], end='')
                entity_buf.clear()
                state_stack.pop()
            elif c in LAST_CHARS_NO_CLOSING and body[i + 1] != ';':
                try:
                    print(RESERVED_ENTITIES[''.join(entity_buf)]['characters'], end='')
                    entity_buf.clear()
                    state_stack.pop()
                    state_stack.append(HtmlParserState.Skip1Char)
                except KeyError:
                    pass
        elif state_stack[-1] == HtmlParserState.Skip1Char:
            pass
