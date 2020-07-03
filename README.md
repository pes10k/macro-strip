macro-strip
===

Just a simple, silly tool for removing (or commenting out) the MACRO
parts of MARCO blocks.  Given the below `example.cc`, you could comment out
the macro control flow with `cat example.cc | ./cli --macro '#if SOME_FLAG'`

```
// example.cc

// #if SOME_FLAG)
std::cout << "this is the good stuff" << std::eol;
// #else
// std::cout << "flag is not enabled" << std::eol;
// #endif
```

or strip ("remove") it all together (but this time the `if` branch) with
`cat example.cc | ./cli --macro '#if SOME_FLAG' -b IF -r`:

```
std::cout << "flag is not enabled" << std::eol;
```

Use
---
```
usage: cli.py [-h] [--file FILE] [--describe] --macro MACRO [--in-place]
              [--remove] [--branch {IF,ELSE,BOTH}]

Strip macro blocks from C/C++.

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  The file to strip macros from. Defaults to stdin.
  --describe, -d        If provided, prints a description of found macros.
                        Does not change the input file. Cannot be used with
                        --in-place.
  --macro MACRO, -m MACRO
                        The full #IF statement of the macro to strip out.
  --in-place, -i        Rewrite the file in place. Cannot be used with
                        --describe.
  --remove, -r          Remove macro lines, instead of commenting out.
  --branch {IF,ELSE,BOTH}, -b {IF,ELSE,BOTH}
                        Set which branch in if / else branches to delete (or
                        comment out). Default is to target ELSE branches. This
                        will only be applied to "if" blocks that have an
                        "else" block too.
```