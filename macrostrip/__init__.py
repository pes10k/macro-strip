from typing import List, Optional, Tuple, Union


from .types import MacroBlock, ControlFlowBranch, ParseState
from .types import IncompleteMacroBlock, GeneralTextIO


GENERIC_MACRO_START = '#if'
GENERIC_MACRO_ELSE = '#else'
GENERIC_MACRO_END = '#endif'


def get_blocks(input: GeneralTextIO, macro: str) -> List[MacroBlock]:
    parse_stack: List[ParseState] = []
    blocks: List[MacroBlock] = []
    current_block = IncompleteMacroBlock()

    def in_target() -> bool:
        return any([x is ParseState.IN_TARGET_IF for x in parse_stack])

    def in_top_target() -> bool:
        count = 0
        for state in parse_stack:
            if state is ParseState.IN_TARGET_IF:
                count += 1
        return count == 1

    def peek() -> ParseState:
        if len(parse_stack) == 0:
            return ParseState.NOT_IN_TARGET_MACRO
        return parse_stack[-1]

    def push(state: ParseState) -> None:
        parse_stack.append(state)

    def pop() -> ParseState:
        return parse_stack.pop()

    def consume_target_if(block: IncompleteMacroBlock, line: str) -> None:
        assert ParseState.is_valid_transition(peek(), ParseState.IN_TARGET_IF)
        if not in_top_target():
            assert block.start_line_num is None
            assert block.else_line_num is None
            block.start_line_num = current_line_num
        block.body += line
        push(ParseState.IN_TARGET_IF)

    def consume_generic_if(block: IncompleteMacroBlock, line: str) -> None:
        assert ParseState.is_valid_transition(peek(), ParseState.IN_IF)
        if in_target():
            block.body += line
        push(ParseState.IN_IF)

    def consume_else(block: IncompleteMacroBlock, line: str) -> None:
        assert ParseState.is_valid_transition(peek(), ParseState.IN_ELSE)
        if in_target():
            block.body += line
            if in_top_target():
                block.else_line_num = current_line_num
        push(ParseState.IN_ELSE)

    def consume_end(block: IncompleteMacroBlock,
                    line: str) -> Optional[IncompleteMacroBlock]:
        current_state = peek()
        assert ParseState.is_valid_transition(current_state, ParseState.IN_END)
        is_in_target = in_target()
        is_top_target = in_top_target()
        pop()

        # If we hit the end block from an else block, we need to push
        # both the else and the if block off the stack, so the extra pop().
        if current_state is ParseState.IN_ELSE:
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


def strip(input: GeneralTextIO, macro: str, comment: bool = False,
          branch: ControlFlowBranch = ControlFlowBranch.IF) -> Tuple[str, int]:
    output_buffer = ""
    blocks = get_blocks(input, macro)
    input.seek(0)

    lines_to_ignore = set()
    for block in blocks:
        lines_to_ignore.add(block.start_line_num)

        if block.has_else():
            else_line_num = block.else_line()
            if branch is ControlFlowBranch.IF:
                body_lines = range(block.start_line_num,
                                   else_line_num + 1)
            elif branch is ControlFlowBranch.ELSE:
                body_lines = range(else_line_num, block.end_line_num)
            else:  # ControlFlowBranch.BOTH condition.
                body_lines = range(block.start_line_num, block.end_line_num)
            lines_to_ignore |= set(body_lines)

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


def describe(input: GeneralTextIO, macro: str) -> str:
    output = ""
    blocks = get_blocks(input, macro)

    for block in blocks:
        output += f"lines: {block.start_line_num} - {block.end_line_num}\n"
        output += block.body
        output += "\n"

    return output


def replace(handle: GeneralTextIO, macro: str, comment: bool = False,
            branch: ControlFlowBranch = ControlFlowBranch.IF) -> int:
    new_text, num_blocks = strip(handle, macro, comment, branch)
    handle.seek(0)
    handle.write(new_text)
    return num_blocks
