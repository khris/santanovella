from enum import StrEnum, auto


class HtmlParserState(StrEnum):
    InTag = auto()
    OutTag = auto()


def show(body: str):
    curr_state = HtmlParserState.OutTag

    for c in body:
        if c == '<':
            curr_state = HtmlParserState.InTag
        elif c == '>':
            curr_state = HtmlParserState.OutTag
        else:
            if curr_state == HtmlParserState.InTag:
                continue
            else:
                print(c, end='')
