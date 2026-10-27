"""Recursive-descent parser over respected lines (one statement per line)."""

from . import errors
from . import nodes as N
from .lexer import LineInfo, Tok

EXPR_START_KW = {
    "facts", "cap", "ghost", "the tea", "hol up", "squad", "empty squad",
    "negative", "nah", "headcount", "from", "ask em", "as words", "as number", "ayo",
}
COMPARE = {"is", "ain't", "under", "over", "at most", "at least"}
ADDITIVE = {"plus", "taxed", "wit"}
MULTIPLICATIVE = {"times", "split", "leftover from"}
PREFIX = {"negative", "headcount", "ask em", "as words", "as number"}
TERMINATORS = {"done", "or if it's", "nah then", "if it go left"}


def describe(tok: Tok | None) -> str:
    if tok is None:
        return "the end of the line"
    if tok.kind == "str":
        return f'"{tok.value}"'
    if tok.kind == "cuh":
        return "a cuh in the middle"
    return f'"{tok.value}"'


class Expr:
    """Parses the tokens of a single line."""

    def __init__(self, tokens: list[Tok], line: int):
        self.toks = tokens
        self.pos = 0
        self.line = line

    def peek(self, offset=0) -> Tok | None:
        i = self.pos + offset
        return self.toks[i] if i < len(self.toks) else None

    def at_kw(self, *values) -> bool:
        t = self.peek()
        return t is not None and t.kind == "kw" and t.value in values

    def next(self) -> Tok:
        t = self.peek()
        if t is None:
            raise errors.syntax(self.line, "the line ended too early")
        self.pos += 1
        return t

    def expect_kw(self, value, after=None):
        t = self.peek()
        if t is None or t.kind != "kw" or t.value != value:
            where = f" after {after}" if after else ""
            raise errors.syntax(self.line, f'expected "{value}"{where}, got {describe(t)}')
        self.pos += 1

    def expect_id(self, what="a name") -> str:
        t = self.peek()
        if t is None or t.kind != "id":
            raise errors.syntax(self.line, f"expected {what}, got {describe(t)}")
        self.pos += 1
        return t.value

    def done(self):
        t = self.peek()
        if t is not None:
            raise errors.syntax(self.line, f"didn't expect {describe(t)}")

    def starts_expr(self) -> bool:
        t = self.peek()
        if t is None:
            return False
        if t.kind in ("num", "str", "id"):
            return True
        return t.kind == "kw" and t.value in EXPR_START_KW

    # precedence climbing, loosest first

    def expr(self) -> N.Node:
        left = self.and_()
        while self.at_kw("or"):
            self.next()
            left = N.BinOp(self.line, "or", left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.at_kw("and"):
            self.next()
            left = N.BinOp(self.line, "and", left, self.not_())
        return left

    def not_(self):
        if self.at_kw("nah"):
            self.next()
            return N.Unary(self.line, "nah", self.not_())
        return self.compare()

    def compare(self):
        left = self.additive()
        if self.peek() and self.peek().kind == "kw" and self.peek().value in COMPARE:
            op = self.next().value
            left = N.BinOp(self.line, op, left, self.additive())
        return left

    def additive(self):
        left = self.multiplicative()
        while self.peek() and self.peek().kind == "kw" and self.peek().value in ADDITIVE:
            op = self.next().value
            left = N.BinOp(self.line, op, left, self.multiplicative())
        return left

    def multiplicative(self):
        left = self.unary()
        while self.peek() and self.peek().kind == "kw" and self.peek().value in MULTIPLICATIVE:
            op = self.next().value
            left = N.BinOp(self.line, op, left, self.unary())
        return left

    def unary(self):
        t = self.peek()
        if t and t.kind == "kw" and t.value in PREFIX:
            self.next()
            return N.Unary(self.line, t.value, self.unary())
        return self.postfix()

    def postfix(self):
        node = self.atom()
        while self.at_kw("spot"):
            self.next()
            node = N.Index(self.line, node, self.atom())
        return node

    def args(self) -> list:
        if not self.starts_expr():
            return []
        out = [self.expr()]
        while self.peek() and self.peek().kind == "comma":
            self.next()
            out.append(self.expr())
        return out

    def atom(self):
        t = self.next()
        if t.kind == "num":
            return N.Num(self.line, t.value)
        if t.kind == "str":
            return N.Str(self.line, t.value)
        if t.kind == "id":
            if self.starts_expr():
                return N.Call(self.line, t.value, self.args(), ayo=False)
            return N.Var(self.line, t.value)
        if t.kind == "kw":
            v = t.value
            if v in ("facts", "cap", "ghost"):
                return N.Lit(self.line, {"facts": True, "cap": False, "ghost": None}[v])
            if v == "the tea":
                return N.Var(self.line, "the tea")
            if v == "hol up":
                inner = self.expr()
                self.expect_kw("aight", "hol up")
                return inner
            if v == "squad":
                return N.Squad(self.line, self.args())
            if v == "empty squad":
                return N.Squad(self.line, [])
            if v == "from":
                start = self.additive()
                self.expect_kw("to", "from")
                return N.Range(self.line, start, self.additive())
            if v == "ayo":
                name = self.expect_id("somebody to call after ayo")
                return N.Call(self.line, name, self.args(), ayo=True)
        raise errors.syntax(self.line, f"didn't expect {describe(t)}")


BLOCK_OPENERS = {"fam", "if it's", "run it back", "long as", "try me"}


class Parser:
    def __init__(self, lines: list[LineInfo]):
        self.lines = [l for l in lines if l.status == "respected"]
        self.i = 0
        self.loops = 0
        self.fams = 0

    def parse(self) -> list:
        body, term = self.block(set())
        if term is not None:
            raise errors.syntax(term.lineno, f'this "{term.tokens[0].value}" ain\'t closing nothing')
        return body

    def head(self, info: LineInfo) -> str | None:
        t = info.tokens[0] if info.tokens else None
        return t.value if t is not None and t.kind == "kw" else None

    def block(self, terminators: set, opener: LineInfo | None = None):
        """Parse statements until a terminator line; returns (body, terminator line)."""
        body = []
        while self.i < len(self.lines):
            info = self.lines[self.i]
            h = self.head(info)
            if h in TERMINATORS:
                if h not in terminators:
                    if opener is None:
                        raise errors.syntax(info.lineno, f'this "{h}" ain\'t closing nothing')
                    raise errors.syntax(info.lineno, f'"{h}" don\'t go here')
                self.i += 1
                if len(info.tokens) != 1 and h != "or if it's":
                    raise errors.syntax(info.lineno, f'"{h}" goes on its own line')
                return body, info
            self.i += 1
            body.append(self.statement(info))
        if opener is not None:
            raise errors.syntax(opener.lineno, "you never said done")
        return body, None

    def statement(self, info: LineInfo) -> N.Stmt:
        line = info.lineno
        e = Expr(info.tokens, line)
        stmt = self._statement(info, e)
        stmt.yell = info.yell
        return stmt

    def _statement(self, info: LineInfo, e: Expr) -> N.Stmt:
        line = info.lineno
        h = self.head(info)

        if h == "cousin":
            e.next()
            name = e.expect_id("a name after cousin")
            e.expect_kw("be", f"cousin {name}")
            value = e.expr()
            e.done()
            return N.Declare(line, name, value)

        if h == "run" and not e.at_kw("run it back"):
            e.next()
            name = e.expect_id("a name after run")
            if e.at_kw("up by"):
                sign = 1
            elif e.at_kw("down by"):
                sign = -1
            else:
                raise errors.syntax(line, f'expected "up by" or "down by" after "run {name}"')
            e.next()
            amount = e.expr()
            e.done()
            return N.Bump(line, name, amount, sign)

        if h in ("say it", "lowkey", "highkey"):
            mode = "normal"
            if h != "say it":
                mode = e.next().value
            e.expect_kw("say it", mode if mode != "normal" else None)
            fr = e.at_kw("fr")
            if fr:
                e.next()
            value = e.expr()
            e.done()
            return N.Say(line, value, fr, mode)

        if h == "fam":
            e.next()
            name = e.expect_id("a name for the fam")
            params = []
            if e.at_kw("takes"):
                e.next()
                params.append(e.expect_id("a parameter name"))
                while e.peek() and e.peek().kind == "comma":
                    e.next()
                    params.append(e.expect_id("a parameter name"))
            e.done()
            saved = self.loops
            self.loops, self.fams = 0, self.fams + 1
            body, _ = self.block({"done"}, info)
            self.loops, self.fams = saved, self.fams - 1
            return N.FamDef(line, name, params, body)

        if h == "pull up with":
            e.next()
            if not self.fams:
                raise errors.syntax(line, "pull up with what? you ain't in a fam")
            value = e.expr() if e.peek() else None
            e.done()
            return N.Return(line, value)

        if h == "if it's":
            branches = []
            otherwise = None
            e.next()
            cond = e.expr()
            e.done()
            while True:
                body, term = self.block({"or if it's", "nah then", "done"}, info)
                branches.append((cond, body))
                th = self.head(term)
                if th == "or if it's":
                    te = Expr(term.tokens, term.lineno)
                    te.next()
                    cond = te.expr()
                    te.done()
                    continue
                if th == "nah then":
                    otherwise, _ = self.block({"done"}, info)
                break
            return N.If(line, branches, otherwise)

        if h == "run it back":
            e.next()
            name = e.expect_id("a name after run it back")
            e.expect_kw("in", f"run it back {name}")
            iterable = e.expr()
            e.done()
            body = self.loop_body(info)
            return N.ForEach(line, name, iterable, body)

        if h == "long as":
            e.next()
            cond = e.expr()
            e.done()
            return N.While(line, cond, self.loop_body(info))

        if h in ("dip", "next up"):
            e.next()
            e.done()
            if not self.loops:
                raise errors.syntax(line, f"{h} from what? you ain't in a loop")
            return N.Break(line) if h == "dip" else N.Continue(line)

        if h == "on cuh":
            e.next()
            cond = e.expr()
            e.done()
            return N.Assert(line, cond)

        if h == "try me":
            e.next()
            e.done()
            body, _ = self.block({"if it go left"}, info)
            handler, _ = self.block({"done"}, info)
            return N.Try(line, body, handler)

        if h == "put":
            e.next()
            item = e.expr()
            e.expect_kw("in", "put")
            target = e.expr()
            e.done()
            return N.Put(line, item, target)

        if h == "kick":
            e.next()
            item = e.expr()
            e.expect_kw("out of", "kick")
            target = e.expr()
            e.done()
            return N.Kick(line, item, target)

        if h == "link up with":
            e.next()
            t = e.next()
            if t.kind != "str":
                raise errors.syntax(line, "link up with needs a file in quotes")
            e.done()
            return N.Link(line, t.value)

        if h in ("no cap", "my bad", "i'm out"):
            e.next()
            e.done()
            if h == "no cap":
                if self.lines[0] is not info:
                    raise errors.syntax(line, "no cap gotta come first")
                return N.NoCap(line)
            return N.Apology(line) if h == "my bad" else N.Exit(line)

        if any(t.kind == "kw" and t.value == "switch up to" for t in info.tokens):
            target = e.postfix()
            if not isinstance(target, (N.Var, N.Index)):
                raise errors.syntax(line, "you can only switch up a name or a spot")
            e.expect_kw("switch up to")
            value = e.expr()
            e.done()
            return N.Assign(line, target, value)

        if not e.starts_expr():
            raise errors.syntax(line, f"didn't expect {describe(e.peek())}")
        expr = e.expr()
        e.done()
        return N.ExprStmt(line, expr)

    def loop_body(self, opener):
        self.loops += 1
        body, _ = self.block({"done"}, opener)
        self.loops -= 1
        return body


def parse(lines: list[LineInfo]) -> list:
    return Parser(lines).parse()
