import enum
import io
from typing import cast, List, Optional, TextIO, Union


GeneralTextIO = Union[TextIO, io.StringIO]


class ControlFlowBranch(enum.Enum):
    IF = enum.auto()
    ELSE = enum.auto()
    BOTH = enum.auto()

    @staticmethod
    def from_string(label: str) -> "ControlFlowBranch":
        return ControlFlowBranch[label]

    @classmethod
    def as_strings(cls) -> List[str]:
        return [o.name for o in cls]


class ParseState(enum.Enum):
    NOT_IN_TARGET_MACRO = enum.auto()
    IN_TARGET_IF = enum.auto()
    IN_IF = enum.auto()
    IN_ELSE = enum.auto()
    IN_END = enum.auto()

    @staticmethod
    def is_valid_transition(from_state: "ParseState",
                            to_state: "ParseState") -> bool:
        return to_state in TRANSITIONS[from_state]


TRANSITIONS = {
    ParseState.NOT_IN_TARGET_MACRO: {ParseState.IN_TARGET_IF,
                                     ParseState.IN_IF,
                                     ParseState.NOT_IN_TARGET_MACRO},
    ParseState.IN_TARGET_IF: {ParseState.IN_TARGET_IF,
                              ParseState.IN_IF,
                              ParseState.IN_ELSE,
                              ParseState.IN_END},
    ParseState.IN_IF: {ParseState.IN_TARGET_IF,
                       ParseState.IN_IF,
                       ParseState.IN_ELSE,
                       ParseState.IN_END},
    ParseState.IN_ELSE: {ParseState.IN_TARGET_IF,
                         ParseState.IN_IF,
                         ParseState.IN_END},
    ParseState.IN_END: {ParseState.NOT_IN_TARGET_MACRO,
                        ParseState.IN_TARGET_IF,
                        ParseState.IN_IF,
                        ParseState.IN_ELSE,
                        ParseState.IN_END}
}


class MacroBlock:
    start_line_num: int
    else_line_num: Optional[int] = None
    end_line_num: int
    body: str = ""

    def __init__(self, start_line: int, else_line: Optional[int],
                 end_line: int, body: str) -> None:
        self.start_line_num = start_line
        self.else_line_num = else_line
        self.end_line_num = end_line
        self.body = body

    def has_else(self) -> bool:
        return self.else_line_num is not None

    def else_line(self) -> int:
        assert self.has_else()
        return cast(int, self.else_line_num)


class IncompleteMacroBlock:
    start_line_num: Optional[int] = None
    else_line_num: Optional[int] = None
    end_line_num: Optional[int] = None
    body: str = ""

    def to_complete(self) -> MacroBlock:
        return MacroBlock(cast(int, self.start_line_num), self.else_line_num,
                          cast(int, self.end_line_num), self.body)
