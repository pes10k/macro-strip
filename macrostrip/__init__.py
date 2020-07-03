import enum
from typing import cast, List, NamedTuple, Optional, TextIO, Tuple


class ParseState(enum.Enum):
    NOT_IN_TARGET_MACRO = enum.auto()
    IN_TARGET_IF = enum.auto()
    IN_IF = enum.auto()
    IN_ELSE = enum.auto()


VALID_PRE_ELSE_STATES = {ParseState.IN_IF, ParseState.IN_TARGET_IF}
VALID_PRE_END_STATES = {ParseState.IN_ELSE, ParseState.IN_IF,
                        ParseState.IN_TARGET_IF}


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


class IncompleteMacroBlock:
    start_line_num: Optional[int] = None
    else_line_num: Optional[int] = None
    end_line_num: Optional[int] = None
    body: str = ""

    def to_complete(self) -> MacroBlock:
        return MacroBlock(cast(int, self.start_line_num), self.else_line_num,
                          cast(int, self.end_line_num), self.body)


GENERIC_MACRO_START = '#if'
GENERIC_MACRO_ELSE = '#else'
GENERIC_MACRO_END = '#endif'


def get_blocks(input: TextIO, macro: str) -> List[MacroBlock]:
    parse_stack: List[ParseState] = []

    def in_target() -> bool:
        return any([x is ParseState.IN_TARGET_IF for x in parse_stack])

    def in_top_target() -> bool:
        count = 0
        for state in parse_stack:
            if state is ParseState.IN_TARGET_IF:
                count += 1
        return count == 1

    def peek() -> Optional[ParseState]:
        if len(parse_stack) == 0:
            return None
        return parse_stack[-1]

    def push(state: ParseState) -> None:
        parse_stack.append(state)

    def pop() -> ParseState:
        return parse_stack.pop()

    blocks: List[MacroBlock] = []
    current_block = IncompleteMacroBlock()

    def consume_target_if(block: IncompleteMacroBlock, line: str) -> None:
        if not in_top_target():
            assert block.start_line_num is None
            assert block.body == ""
            assert block.else_line_num is None
            block.start_line_num = current_line_num
        block.body += line
        push(ParseState.IN_TARGET_IF)

    def consume_generic_if(block: IncompleteMacroBlock, line: str) -> None:
        current_state = peek()
        if current_state is not None:
            block.body += line
        push(ParseState.IN_IF)

    def consume_else(block: IncompleteMacroBlock, line: str) -> None:
        current_state = peek()
        assert current_state in VALID_PRE_ELSE_STATES
        if in_target():
            block.body += line
            if in_top_target():
                block.else_line_num = current_line_num
        push(ParseState.IN_ELSE)

    def consume_end(block: IncompleteMacroBlock,
                    line: str) -> Optional[IncompleteMacroBlock]:
        current_state = peek()
        assert current_state in VALID_PRE_END_STATES
        if current_state is ParseState.IN_ELSE:
            pop()
        is_in_target = in_target()
        is_top_target = in_top_target()
        pop()
        if is_in_target:
            assert block.start_line_num is not None
            block.body += line
            if is_top_target:
                block.end_line_num = current_line_num
                blocks.append(block.to_complete())
                return IncompleteMacroBlock()
        return None

    def consume_other_line(block: IncompleteMacroBlock, line: str) -> None:
        if in_top_target():
            block.body += line

    current_line_num = 0
    for line in input:
        current_line_num += 1
        if line.startswith(macro):
            consume_target_if(current_block, line)
        elif line.startswith(GENERIC_MACRO_START):
            consume_generic_if(current_block, line)
        elif line.startswith(GENERIC_MACRO_ELSE):
            consume_else(current_block, line)
        elif line.startswith(GENERIC_MACRO_END):
            possible_finished_block = consume_end(current_block, line)
            if possible_finished_block is not None:
                current_block = possible_finished_block
        else:
            consume_other_line(current_block, line)

    return blocks


def strip(input: TextIO, macro: str, comment: bool = False) -> Tuple[str, int]:
    output_buffer = ""
    blocks = get_blocks(input, macro)
    input.seek(0)

    lines_to_ignore = set()
    for block in blocks:
        lines_to_ignore.add(block.start_line_num)
        if block.else_line_num is not None:
            else_block_lines = range(block.else_line_num, block.end_line_num)
            lines_to_ignore |= set(else_block_lines)
        lines_to_ignore.add(block.end_line_num)

    line_num = 0
    for line in input:
        line_num += 1
        if line_num in lines_to_ignore:
            if comment:
                output_buffer += "// " + line
            continue
        output_buffer += line

    return (output_buffer, len(blocks))


def describe(input: TextIO, macro: str) -> str:
    output = ""
    blocks = get_blocks(input, macro)

    for block in blocks:
        output += f"lines: {block.start_line_num} - {block.end_line_num}\n"
        output += block.body
        output += "\n"

    return output


def replace(handle: TextIO, macro: str, comment: bool = False) -> int:
    new_text, num_blocks = strip(handle, macro, comment)
    handle.seek(0)
    handle.write(new_text)
    return num_blocks
