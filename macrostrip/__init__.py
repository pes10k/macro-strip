import collections
from typing import List, NamedTuple, TextIO, Tuple


class MacroBlock(NamedTuple):
    start: int
    end: int
    body: str
    additional: List[int] = []


MACRO_START = '#if'
MACRO_ELSE = '#else'
MACRO_END = '#endif'


def get_blocks(input: TextIO, macro: str) -> List[MacroBlock]:
    blocks = []
    line_num = 0

    macro_stack = 0

    buffer = ""
    additional_lines = []
    start_line_num = -1
    in_else = False

    def reset_temp_block() -> None:
        buffer = ""
        additional_lines: List[int] = []
        start_line_num = -1
        in_else = False

    in_block = False

    for row in input:
        line_num += 1
        if row.startswith(macro):
            if not in_block:
                start_line_num = line_num
                buffer += row
                macro_stack += 1
                in_block = True
            else:
                macro_stack += 1
                buffer += row
            continue

        if row.startswith(MACRO_START) and in_block:
            macro_stack += 1
            buffer += row
            continue

        if row.startswith(MACRO_ELSE) and in_block:
            in_else = True
            additional_lines.append(line_num)
            buffer += row
            continue

        if row.startswith(MACRO_END) and in_block:
            buffer += row
            macro_stack -= 1
            if macro_stack == 0:
                finished_block = MacroBlock(start_line_num, line_num,
                                            buffer, additional_lines)
                blocks.append(finished_block)
                reset_temp_block()
                in_block = False
            continue

        if in_else:
            additional_lines.append(line_num)
            buffer += row
            continue

        if in_block:
            buffer += row

    return blocks


def strip(input: TextIO, macro: str, comment: bool = False) -> Tuple[str, int]:
    output_buffer = ""
    blocks = get_blocks(input, macro)
    input.seek(0)

    lines_to_ignore = set()
    for block in blocks:
        lines_to_ignore.add(block.start)
        lines_to_ignore.add(block.end)

    line_num = 0
    for row in input:
        line_num += 1
        if line_num in lines_to_ignore:
            if comment:
                output_buffer += "// " + row
            continue
        output_buffer += row

    return (output_buffer, len(blocks))


def describe(input: TextIO, macro: str) -> str:
    output_buffer = ""
    blocks = get_blocks(input, macro)

    for block in blocks:
        output_buffer += f"lines: {block.start} - {block.end}\n"
        output_buffer += block.body
        output_buffer += "\n"

    return output_buffer


def replace(handle: TextIO, macro: str, comment: bool = False) -> int:
    new_text, num_blocks = strip(handle, macro, comment)
    handle.seek(0)
    handle.write(new_text)
    return num_blocks
