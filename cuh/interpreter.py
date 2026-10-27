"""Tree-walking evaluator with a mood."""

import difflib
import hashlib
import os
import random
import sys
from fractions import Fraction

from . import errors
from . import nodes as N
from .errors import CuhError
from .lexer import analyze
from .parser import parse
from .respect import judge

MAX_DEPTH = 500
HELPFUL = Fraction(9, 10)
RANDOM_CUH = 0.1


class Fam:
    def __init__(self, name, params, body, closure):
        self.name, self.params, self.body, self.closure = name, params, body, closure


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ExitSignal(Exception):
    pass


class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        return None

    def names(self):
        out, env = set(), self
        while env is not None:
            out |= env.vars.keys()
            env = env.parent
        return out


def seed_for(source: str) -> int:
    return int.from_bytes(hashlib.sha256(source.encode()).digest()[:8], "big")


# value helpers

def type_name(v):
    if isinstance(v, bool):
        return "facts or cap"
    if isinstance(v, (int, float)):
        return "a number"
    if isinstance(v, str):
        return "words"
    if isinstance(v, list):
        return "a squad"
    if v is None:
        return "ghost"
    if isinstance(v, Fam):
        return "a fam"
    return "something"


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def tidy(v):
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def show(v, nested=False) -> str:
    if isinstance(v, bool):
        return "facts" if v else "cap"
    if v is None:
        return "ghost"
    if isinstance(v, float):
        return repr(tidy(v))
    if isinstance(v, str):
        return '"' + v + '"' if nested else v
    if isinstance(v, list):
        if not v:
            return "empty squad"
        text = "squad " + ", ".join(show(x, True) for x in v)
        return f"hol up {text} aight" if nested else text
    if isinstance(v, Fam):
        return f"fam {v.name}"
    return str(v)


def same(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if is_num(a) and is_num(b):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def sulk(text: str) -> str:
    return "".join(c for c in text.lower() if c.isalnum() or c.isspace())


class Interpreter:
    def __init__(self, out=None, err=None, inp=None, seed=0, respect=Fraction(1), base_dir="."):
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        self.inp = inp or sys.stdin
        self.rng = random.Random(seed)
        self.respect = respect
        self.yells = 0
        self.nocap = False
        self.depth = 0
        self.globals = Env()
        self.base_dirs = [base_dir]
        self.linked = set()

    # mood

    @property
    def sulking(self):
        return self.yells >= 3

    @property
    def mood(self):
        if self.sulking:
            return "sulk"
        return "helpful" if self.respect >= HELPFUL else "stock"

    def render(self, e: CuhError) -> str:
        return e.render(self.mood)

    # statements

    def run(self, program: list, env=None):
        self.exec_block(program, env or self.globals)

    def exec_block(self, body, env):
        for stmt in body:
            self.exec(stmt, env)

    def exec(self, s: N.Stmt, env: Env):
        if s.yell:
            self.yells += 1
        return getattr(self, "exec_" + type(s).__name__)(s, env)

    def exec_Declare(self, s, env):
        env.vars[s.name] = self.eval(s.value, env)

    def exec_Assign(self, s, env):
        value = self.eval(s.value, env)
        if isinstance(s.target, N.Var):
            owner = env.find(s.target.name)
            if owner is None:
                raise self.undefined(s.target.name, s.line, env)
            owner.vars[s.target.name] = value
        else:
            seq = self.eval(s.target.target, env)
            i = self.position(seq, self.eval(s.target.index, env), s.target, env)
            if isinstance(seq, str):
                raise errors.type_error("switch up", "letters in", "", "words", s.line)
            seq[i] = value

    def exec_Bump(self, s, env):
        owner = env.find(s.name)
        if owner is None:
            raise self.undefined(s.name, s.line, env)
        amount = self.eval(s.amount, env)
        current = owner.vars[s.name]
        if not (is_num(current) and is_num(amount)):
            raise errors.type_error("run up", type_name(current), "by", type_name(amount), s.line)
        owner.vars[s.name] = tidy(current + s.sign * amount)

    def exec_Say(self, s, env):
        text = show(self.eval(s.value, env))
        if s.mode == "highkey":
            self.yells += 1
            text = text.upper()
        if not (s.fr or self.nocap) and self.rng.random() < RANDOM_CUH:
            text += " cuh"
        if self.sulking:
            text = sulk(text)
        stream = self.err if s.mode == "lowkey" else self.out
        stream.write(text + "\n")

    def exec_FamDef(self, s, env):
        env.vars[s.name] = Fam(s.name, s.params, s.body, env)

    def exec_Return(self, s, env):
        raise ReturnSignal(None if s.value is None else self.eval(s.value, env))

    def exec_ExprStmt(self, s, env):
        value = self.eval(s.expr, env)
        if isinstance(s.expr, N.Var) and isinstance(value, Fam):
            self.call(value, [], False, s.line)
        return value

    def exec_If(self, s, env):
        for cond, body in s.branches:
            if self.eval(cond, env):
                return self.exec_block(body, env)
        if s.otherwise is not None:
            self.exec_block(s.otherwise, env)

    def exec_ForEach(self, s, env):
        items = self.eval(s.iterable, env)
        if not isinstance(items, (list, str)):
            raise errors.type_error("run it back in", type_name(items), "", "", s.line)
        for item in list(items):
            env.vars[s.name] = item
            try:
                self.exec_block(s.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def exec_While(self, s, env):
        while self.eval(s.cond, env):
            try:
                self.exec_block(s.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def exec_Break(self, s, env):
        raise BreakSignal()

    def exec_Continue(self, s, env):
        raise ContinueSignal()

    def exec_Assert(self, s, env):
        if not self.eval(s.cond, env):
            raise errors.lied(s.line)

    def exec_Try(self, s, env):
        try:
            self.exec_block(s.body, env)
        except CuhError as e:
            env.vars["the tea"] = e.msg
            self.exec_block(s.handler, env)

    def exec_Put(self, s, env):
        item = self.eval(s.item, env)
        target = self.eval(s.target, env)
        if not isinstance(target, list):
            raise errors.type_error("put stuff in", type_name(target), "", "", s.line)
        target.append(item)

    def exec_Kick(self, s, env):
        item = self.eval(s.item, env)
        target = self.eval(s.target, env)
        if not isinstance(target, list):
            raise errors.type_error("kick stuff out of", type_name(target), "", "", s.line)
        for i, x in enumerate(target):
            if same(x, item):
                del target[i]
                return
        raise errors.not_in(show(item, True), s.line)

    def exec_Link(self, s, env):
        path = os.path.normpath(os.path.join(self.base_dirs[-1], s.path))
        if path in self.linked:
            return
        try:
            with open(path, encoding="utf-8") as f:
                source = f.read()
        except OSError:
            raise errors.missing_import(s.path, s.line) from None
        lines = analyze(source)
        if judge(lines).verdict != "ok":
            raise errors.disrespected_import(s.path, s.line)
        program = parse(lines)
        self.linked.add(path)
        self.base_dirs.append(os.path.dirname(path))
        try:
            self.run(program, self.globals)
        finally:
            self.base_dirs.pop()

    def exec_NoCap(self, s, env):
        self.nocap = True

    def exec_Apology(self, s, env):
        self.yells = max(0, self.yells - 1)

    def exec_Exit(self, s, env):
        raise ExitSignal()

    # expressions

    def undefined(self, name, line, env):
        guess = difflib.get_close_matches(name, sorted(env.names()), n=1, cutoff=0.6)
        return errors.undefined(name, line, guess[0] if guess else None)

    def eval(self, e: N.Node, env: Env):
        return getattr(self, "eval_" + type(e).__name__)(e, env)

    def eval_Num(self, e, env):
        return e.value

    def eval_Str(self, e, env):
        return e.value

    def eval_Lit(self, e, env):
        return e.value

    def eval_Var(self, e, env):
        owner = env.find(e.name)
        if owner is None:
            raise self.undefined(e.name, e.line, env)
        return owner.vars[e.name]

    def eval_Squad(self, e, env):
        return [self.eval(x, env) for x in e.items]

    def eval_Range(self, e, env):
        a, b = self.eval(e.start, env), self.eval(e.end, env)
        if not (isinstance(a, int) and isinstance(b, int)) or isinstance(a, bool) or isinstance(b, bool):
            raise errors.type_error("count from", type_name(a), "to", type_name(b), e.line)
        step = 1 if b >= a else -1
        return list(range(a, b + step, step))

    def eval_Unary(self, e, env):
        if e.op == "nah":
            return not self.eval(e.operand, env)
        v = self.eval(e.operand, env)
        if e.op == "negative":
            if not is_num(v):
                raise errors.type_error("make", type_name(v), "", "negative", e.line)
            return -v
        if e.op == "headcount":
            if not isinstance(v, (list, str)):
                raise errors.type_error("headcount", type_name(v), "", "", e.line)
            return len(v)
        if e.op == "as words":
            return show(v)
        if e.op == "as number":
            if is_num(v):
                return v
            text = show(v).strip()
            try:
                return int(text)
            except ValueError:
                try:
                    return tidy(float(text))
                except ValueError:
                    raise errors.not_a_number(text, e.line) from None
        if e.op == "ask em":
            self.out.write(show(v))
            self.out.flush()
            line = self.inp.readline()
            return line.rstrip("\n") if line else None
        raise AssertionError(e.op)

    def eval_BinOp(self, e, env):
        op = e.op
        if op == "and":
            left = self.eval(e.left, env)
            return self.eval(e.right, env) if left else left
        if op == "or":
            left = self.eval(e.left, env)
            return left if left else self.eval(e.right, env)
        a, b = self.eval(e.left, env), self.eval(e.right, env)
        if op == "wit":
            return show(a) + show(b)
        if op == "is":
            return same(a, b)
        if op == "ain't":
            return not same(a, b)
        if op in ("under", "over", "at most", "at least"):
            if not ((is_num(a) and is_num(b)) or (isinstance(a, str) and isinstance(b, str))):
                raise errors.type_error("compare", type_name(a), "to", type_name(b), e.line)
            return {"under": a < b, "over": a > b, "at most": a <= b, "at least": a >= b}[op]
        if op == "plus":
            if is_num(a) and is_num(b):
                return tidy(a + b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            if isinstance(a, str) and isinstance(b, str):
                return a + b
            raise errors.type_error("add", type_name(b), "to", type_name(a), e.line)
        if op == "times":
            if is_num(a) and is_num(b):
                return tidy(a * b)
            if isinstance(a, (str, list)) and isinstance(b, int) and not isinstance(b, bool):
                return a * b
            raise errors.type_error("multiply", type_name(a), "by", type_name(b), e.line)
        if not (is_num(a) and is_num(b)):
            verb = {"taxed": ("tax", "by"), "split": ("split", "by"), "leftover from": ("split", "by")}[op]
            raise errors.type_error(verb[0], type_name(a), verb[1], type_name(b), e.line)
        if op == "taxed":
            return tidy(a - b)
        if b == 0:
            raise errors.zero(e.line)
        if op == "split":
            return a // b if isinstance(a, int) and isinstance(b, int) and a % b == 0 else tidy(a / b)
        return tidy(a % b)

    def position(self, seq, index, node, env):
        if not isinstance(seq, (list, str)):
            raise errors.type_error("spot", type_name(seq), "", "", node.line)
        if not isinstance(index, int) or isinstance(index, bool):
            raise errors.type_error("spot", type_name(seq), "with", type_name(index), node.line)
        if not 1 <= index <= len(seq):
            who = node.target.name if isinstance(node.target, N.Var) else "that"
            unit = "letters" if isinstance(seq, str) else "people"
            raise errors.out_of_range(who, len(seq), unit, node.line)
        return index - 1

    def eval_Index(self, e, env):
        seq = self.eval(e.target, env)
        return seq[self.position(seq, self.eval(e.index, env), e, env)]

    def eval_Call(self, e, env):
        owner = env.find(e.name)
        if owner is None:
            raise self.undefined(e.name, e.line, env)
        fam = owner.vars[e.name]
        if not isinstance(fam, Fam):
            raise errors.not_fam(e.name, e.line)
        args = [self.eval(a, env) for a in e.args]
        return self.call(fam, args, e.ayo, e.line)

    def call(self, fam: Fam, args, ayo, line):
        if len(args) != len(fam.params):
            raise errors.arity(fam.name, len(fam.params), len(args), line)
        if self.depth >= MAX_DEPTH:
            raise errors.tired(line)
        env = Env(fam.closure)
        env.vars.update(zip(fam.params, args))
        self.depth += 1
        try:
            self.exec_block(fam.body, env)
            result = None
        except ReturnSignal as r:
            result = r.value
        finally:
            self.depth -= 1
        return result if ayo else None


def run_source(source: str, path: str = "<cuh>", out=None, err=None, inp=None, seed=None) -> int:
    """Lex, judge, parse and run a program. Returns the exit code."""
    err = err or sys.stderr
    lines = analyze(source)
    report = judge(lines)
    for w in report.warnings:
        err.write(w + "\n")
    if report.verdict != "ok":
        err.write(report.message + "\n")
        return report.exit_code
    interp = Interpreter(out, err, inp, seed_for(source) if seed is None else seed,
                         report.respect, os.path.dirname(os.path.abspath(path)))
    if path != "<cuh>":
        interp.linked.add(os.path.normpath(os.path.abspath(path)))
    try:
        program = parse(lines)
    except CuhError as e:
        err.write(interp.render(e) + "\n")
        return 1
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, 20000))
    try:
        interp.run(program)
    except ExitSignal:
        pass
    except CuhError as e:
        err.write(interp.render(e) + "\n")
        return 1
    except RecursionError:
        err.write(interp.render(errors.tired(0)) + "\n")
        return 1
    finally:
        sys.setrecursionlimit(old_limit)
    return 0
