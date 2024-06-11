import re
import sys

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Final, Self

class JSONType(Enum):
    Number = 0
    String = 1
    Null = 2
    Bool = 3
    List = 4
    Object = 5



@dataclass
class JSONNode:
    type: JSONType
    value: bytes | list[Self] | list[list[Self]]


def _parse_with_pattern(data: bytes, pattern: re.Pattern[bytes]) -> tuple[bytes, bytes]:
    m: re.Match[bytes] | None = re.match(pattern, data)
    if m is None or m.start() != 0:
        raise ValueError
    return (data[m.start():m.end()], data[m.end():])


_NUMBER_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A[0-9_\.e+\-]+")
def parse_number(data: bytes) -> tuple[JSONNode, bytes]:
    consumed, remaining = _parse_with_pattern(data, _NUMBER_RE)
    return (JSONNode(JSONType.Number, consumed), remaining)


_NULL_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A[Nn][Uu][Ll][Ll]")
def parse_null(data: bytes) -> tuple[JSONNode, bytes]:
    consumed, remaining = _parse_with_pattern(data, _NULL_RE)
    return (JSONNode(JSONType.Null, consumed), remaining)


# This works due to a nice property of UTF-8: no code point's UTF-8 representation contains '\x22', except '\x22' == '"' itself.
_STRING_RE: Final[re.Pattern[bytes]] = re.compile(rb'\A"(:?[^"\\]|\\.)*"' + b"|" + rb"\A\'(:?[^'\\]|\\.)*\'")
def parse_string(data: bytes) -> tuple[JSONNode, bytes]:
    consumed, remaining = _parse_with_pattern(data, _STRING_RE)
    return (JSONNode(JSONType.String, consumed), remaining)


_BOOL_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A[Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee]")
def parse_bool(data: bytes) -> tuple[JSONNode, bytes]:
    consumed, remaining = _parse_with_pattern(data, _BOOL_RE)
    return (JSONNode(JSONType.Bool, consumed), remaining)


_WHITESPACE_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A[\x09-\x0d\x1c-\x1f\x20\x85\xa0]*")
def consume_whitespace(data: bytes) -> bytes:
    return _parse_with_pattern(data, _WHITESPACE_RE)[1]


_COMMA_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A,")
def consume_comma(data: bytes) -> bytes:
    return _parse_with_pattern(data, _COMMA_RE)[1]


_OPEN_BRACKET_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A\[")
def consume_open_bracket(data: bytes) -> bytes:
    return _parse_with_pattern(data, _OPEN_BRACKET_RE)[1]


_CLOSE_BRACKET_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A\]")
def consume_close_bracket(data: bytes) -> bytes:
    return _parse_with_pattern(data, _CLOSE_BRACKET_RE)[1]


_OPEN_CURLY_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A\{")
def consume_open_curly(data: bytes) -> bytes:
    return _parse_with_pattern(data, _OPEN_CURLY_RE)[1]


_CLOSE_CURLY_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A\}")
def consume_close_curly(data: bytes) -> bytes:
    return _parse_with_pattern(data, _CLOSE_CURLY_RE)[1]


_COLON_RE: Final[re.Pattern[bytes]] = re.compile(rb"\A:")
def consume_colon(data: bytes) -> bytes:
    return _parse_with_pattern(data, _COLON_RE)[1]


def parse_expression(data: bytes) -> tuple[JSONNode, bytes]:
    for f in (parse_number, parse_null, parse_string, parse_bool, parse_list, parse_object):
        try:
            return f(data)
        except ValueError:
            pass
    raise ValueError


def parse_list(data: bytes) -> tuple[JSONNode, bytes]:
    data = consume_open_bracket(data)

    result: list[JSONNode] = []
    while True:
        data = consume_whitespace(data)

        try:
            item, data = parse_expression(data)
            result.append(item)
        except ValueError:
            pass

        data = consume_whitespace(data)
        
        try:
            data = consume_comma(data)
        except ValueError:
            pass

        data = consume_whitespace(data)

        try:
            data = consume_close_bracket(data)
            break
        except ValueError:
            pass

    return (JSONNode(JSONType.List, result), data)


def parse_object(data: bytes) -> tuple[JSONNode, bytes]:
    data = consume_open_curly(data)

    result: list[list[JSONNode]] = []
    while True:
        # Eat values separated by colons until there's no colon
        kvp: list[JSONNode] = []
        while True:
            data = consume_whitespace(data)
            item, data = parse_expression(data)
            kvp.append(item)
            data = consume_whitespace(data)
            try:
                data = consume_colon(data)
            except:
                break
        if len(kvp) > 0:
            result.append(kvp)
        
        # Optionally eat a comma
        try:
            data = consume_comma(data)
        except ValueError:
            pass
        data = consume_whitespace(data)

        # If we hit a close curly, break
        try:
            data = consume_close_curly(data)
            break
        except ValueError:
            pass

    return (JSONNode(JSONType.Object, result), data)

if __name__ == "__main__":
    print(parse_expression(sys.stdin.buffer.read()))
