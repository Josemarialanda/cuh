"""Command line: cuh run FILE [--seed N] | cuh check FILE | cuh FILE | cuh"""

import sys

from .interpreter import run_source
from .lexer import analyze
from .repl import repl
from .respect import judge, report_text

USAGE = """usage:
  cuh                       start the REPL
  cuh FILE                  run a program
  cuh run FILE [--seed N]   run a program with a fixed vibe
  cuh check FILE            show the respect report
"""


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        sys.stderr.write(f'can\'t find "{path}" cuh, where it at\n')
        sys.exit(1)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return repl()
    if args[0] in ("-h", "--help", "help"):
        sys.stdout.write(USAGE)
        return 0

    cmd = args.pop(0)
    if cmd == "check":
        if len(args) != 1:
            sys.stderr.write(USAGE)
            return 64
        report = judge(analyze(read(args[0])))
        sys.stdout.write(report_text(report) + "\n")
        for w in report.warnings:
            sys.stderr.write(w + "\n")
        return report.exit_code

    if cmd != "run":
        args.insert(0, cmd)
    seed = None
    if "--seed" in args:
        i = args.index("--seed")
        try:
            seed = int(args[i + 1])
        except (IndexError, ValueError):
            sys.stderr.write("--seed needs a number cuh\n")
            return 64
        del args[i:i + 2]
    if len(args) != 1:
        sys.stderr.write(USAGE)
        return 64
    return run_source(read(args[0]), args[0], seed=seed)


if __name__ == "__main__":
    sys.exit(main())
