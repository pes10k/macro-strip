#!/usr/bin/env python3
import argparse
import io
import sys

import macrostrip
from macrostrip.types import ControlFlowBranch, GeneralTextIO


PARSER = argparse.ArgumentParser(description='Strip macro blocks from C/C++.')
PARSER.add_argument('--file', '-f', default=None,
                    help='The file to strip macros from. Defaults to stdin.')
PARSER.add_argument('--describe', '-d', action='store_true',
                    help='If provided, prints a description of found macros. '
                         'Does not change the input file. Cannot be used with '
                         '--in-place.')
PARSER.add_argument('--macro', '-m', required=True,
                    help='The full #IF statement of the macro to strip out.')
PARSER.add_argument('--in-place', '-i', action='store_true',
                    help='Rewrite the file in place. Cannot be used with '
                         '--describe.')
PARSER.add_argument('--remove', '-r', action='store_true',
                    help='Remove macro lines, instead of commenting out.')
PARSER.add_argument('--branch', '-b', default=ControlFlowBranch.ELSE.name,
                    choices=ControlFlowBranch.as_strings(),
                    help='Set which branch in if / else branches to delete '
                         '(or comment out).  Default is to target '
                         f'{ControlFlowBranch.ELSE.name} branches. This will '
                         'only be applied to "if" blocks that have an "else" '
                         'block too.')
ARGS = PARSER.parse_args()
INPUT: GeneralTextIO
BRANCH = ControlFlowBranch.from_string(ARGS.branch)

if not ARGS.file:
    IS_STDOUT = True
    INPUT = io.StringIO(sys.stdin.read())
else:
    IS_STDOUT = False
    if ARGS.in_place:
        INPUT = open(ARGS.file, 'r+t')
    else:
        INPUT = open(ARGS.file, 'rt')

if ARGS.describe and ARGS.in_place:
    print("Cannot use --in-place with --describe", file=sys.stderr)
    sys.exit(1)

if ARGS.describe:
    print(macrostrip.describe(INPUT, ARGS.macro))
    sys.exit(0)

SHOULD_COMMENT_OUT = not ARGS.remove

if ARGS.in_place:
    if IS_STDOUT:
        print("Cannot rewrite in place with stdio", file=sys.stderr)
        sys.exit(1)

    NUM_BLOCKS = macrostrip.replace(INPUT, ARGS.macro,
                                    comment=SHOULD_COMMENT_OUT,
                                    branch=BRANCH)
    if IS_STDOUT:
        print(f"Replace {NUM_BLOCKS} macro blocks")

    sys.exit(0)

NEW_TEXT, NUM_BLOCKS = macrostrip.strip(INPUT, ARGS.macro,
                                        comment=SHOULD_COMMENT_OUT,
                                        branch=BRANCH)
print(NEW_TEXT)
