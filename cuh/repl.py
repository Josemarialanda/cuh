"""The cuh REPL: the prompt shows a rolling respect score."""

import sys
from collections import deque

from . import nodes as N
from .errors import CuhError
from .interpreter import ExitSignal, Interpreter, show
from .lexer import analyze_line
from .parser import BLOCK_OPENERS, parse
from .respect import THRESHOLD, judge

WINDOW = 20
GRACE = 4  # lines before the REPL starts enforcing respect


def repl(inp=None, out=None, err=None) -> int:
    inp = inp or sys.stdin
    out = out or sys.stdout
    err = err or sys.stderr
    interp = Interpreter(out, err, inp, seed=0)
    window: deque = deque(maxlen=WINDOW)
    buffer = []
    depth = 0
    lineno = 0

    while True:
        report = judge(list(window))
        out.write(f"cuh({report.percent}%)> " if not buffer else "  ...> ")
        out.flush()
        text = inp.readline()
        if not text:
            out.write("\n")
            return 0
        lineno += 1
        info = analyze_line(text.rstrip("\n"), lineno)
        if info.status == "blank":
            continue

        window.append(info)
        report = judge(list(window))
        if report.verdict == "spam":
            window.pop()
            err.write(report.message + "\n")
            continue
        if report.respect < THRESHOLD and len(window) >= GRACE:
            out.write(f"i'm out. (respect: {report.percent}%)\n")
            return 2
        if info.status == "skipped":
            out.write("...?\n")
            continue
        if info.status == "bare":
            continue

        head = info.tokens[0].value if info.tokens and info.tokens[0].kind == "kw" else None
        if head in BLOCK_OPENERS:
            depth += 1
        elif head == "done":
            depth -= 1
        buffer.append(info)
        if depth > 0:
            continue

        lines, buffer, depth = buffer, [], 0
        interp.respect = report.respect
        try:
            for stmt in parse(lines):
                value = interp.exec(stmt, interp.globals)
                if isinstance(stmt, N.ExprStmt) and value is not None:
                    out.write(show(value) + "\n")
        except ExitSignal:
            return 0
        except CuhError as e:
            err.write(interp.render(e) + "\n")
        except RecursionError:
            err.write("i'm tired cuh\n")
