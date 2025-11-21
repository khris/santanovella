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
    EntityReserved = auto()
    EntityCodepoint = auto()
    EntityCodepointHex = auto()
    Skip1Char = auto()


def show(body: str):
    state_stack = [HtmlParserState.Default]
    tag_buf = []
    entity_buf = []

    for i, c in enumerate(body):
        match (state_stack[-1]):
            case HtmlParserState.Default:
                if c == '<':
                    state_stack.append(HtmlParserState.Tag)
                elif c == '&':
                    state_stack.append(HtmlParserState.EntityReserved)
                    entity_buf.append(c)
                else:
                    print(c, end='')

            case HtmlParserState.Tag:
                if c == '>':
                    tag_buf.clear()
                    state_stack.pop()
                else:
                    tag_buf.append(c)

            case HtmlParserState.EntityReserved:
                if c == '#':
                    entity_buf.pop()
                    state_stack.pop()
                    state_stack.append(HtmlParserState.EntityCodepoint)
                    continue

                entity_buf.append(c)
                if c == ';':
                    print(RESERVED_ENTITIES[''.join(entity_buf)]['characters'],
                          end='')
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

            case HtmlParserState.EntityCodepoint:
                if c == 'x':
                    state_stack.pop()
                    state_stack.append(HtmlParserState.EntityCodepointHex)
                    continue

                if c == ';':
                    print(chr(int(''.join(entity_buf))), end='')
                    entity_buf.clear()
                    state_stack.pop()
                else:
                    entity_buf.append(c)

            case HtmlParserState.EntityCodepointHex:
                if c == ';':
                    print(chr(int(''.join(entity_buf), base=16)), end='')
                    entity_buf.clear()
                    state_stack.pop()
                else:
                    entity_buf.append(c)

            case HtmlParserState.Skip1Char:
                pass
