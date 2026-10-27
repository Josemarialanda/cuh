"""Lexer: turns source into per-line token lists and cuh stats.

Every line is lexed (even skipped ones) so the respect check can count cuhs.
Strings are read first, so a "cuh" inside quotes never counts.
"""

from dataclasses import dataclass, field

# Multi-word keywords, matched longest-first. Single words are phrases of one.
PHRASES = [
    "say it", "lowkey", "highkey", "fr",
    "cousin", "be", "switch up to", "run", "up by", "down by",
    "fam", "takes", "pull up with", "ayo", "done",
    "if it's", "or if it's", "nah then",
    "run it back", "in", "long as", "dip", "next up",
    "on cuh", "try me", "if it go left", "the tea",
    "put", "kick", "out of", "link up with", "no cap", "my bad", "i'm out",
    "plus", "wit", "taxed", "times", "split", "leftover from", "negative",
    "is", "ain't", "under", "over", "at most", "at least",
    "and", "or", "nah", "hol up", "aight",
    "spot", "squad", "empty squad",
    "headcount", "from", "to", "ask em", "as words", "as number",
    "facts", "cap", "ghost",
]

_BY_FIRST: dict[str, list[tuple[str, ...]]] = {}
for _p in PHRASES:
    _words = tuple(_p.split())
    _BY_FIRST.setdefault(_words[0], []).append(_words)
for _v in _BY_FIRST.values():
    _v.sort(key=len, reverse=True)


@dataclass
class Tok:
    kind: str  # str, num, word, comma, other, cuh, kw, id
    value: object
    line: int

    def __repr__(self):
        return f"{self.kind}:{self.value!r}"


@dataclass
class LineInfo:
    lineno: int
    text: str
    status: str  # blank, respected, skipped, bare
    cuhs: int = 0
    yell: bool = False
    tokens: list[Tok] = field(default_factory=list)  # statement tokens (respected only)

    @property
    def is_apology(self):
        return _only_kw(self.tokens, "my bad")

    @property
    def is_nocap(self):
        return _only_kw(self.tokens, "no cap")


def _only_kw(tokens, phrase):
    return len(tokens) == 1 and tokens[0].kind == "kw" and tokens[0].value == phrase


def _is_word_char(c):
    return c.isalnum() or c in "_'"


def lex_line(text: str, lineno: int) -> list[Tok]:
    """Raw tokens for one line. Never fails; junk becomes 'other' tokens."""
    text = text.replace("’", "'").replace("‘", "'")
    toks: list[Tok] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == '"':
            i += 1
            buf = []
            closed = False
            while i < n:
                ch = text[i]
                if ch == "\\" and i + 1 < n:
                    buf.append({"n": "\n", "t": "\t"}.get(text[i + 1], text[i + 1]))
                    i += 2
                elif ch == '"':
                    closed = True
                    i += 1
                    break
                else:
                    buf.append(ch)
                    i += 1
            toks.append(Tok("str" if closed else "other", "".join(buf), lineno))
        elif c.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            if j + 1 < n and text[j] == "." and text[j + 1].isdigit():
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
                toks.append(Tok("num", float(text[i:j]), lineno))
            else:
                toks.append(Tok("num", int(text[i:j]), lineno))
            i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < n and _is_word_char(text[j]):
                j += 1
            word = text[i:j]
            if word in ("cuh", "CUH"):
                toks.append(Tok("cuh", word, lineno))
            else:
                toks.append(Tok("word", word, lineno))
            i = j
        elif c == ",":
            toks.append(Tok("comma", ",", lineno))
            i += 1
        else:
            toks.append(Tok("other", c, lineno))
            i += 1
    return toks


def _word_of(tok):
    if tok.kind == "word":
        return tok.value
    if tok.kind == "cuh":
        return "cuh"
    return None


def combine(raw: list[Tok]) -> list[Tok]:
    """Merge words into keyword phrases (longest match); other words are ids."""
    out: list[Tok] = []
    i = 0
    while i < len(raw):
        tok = raw[i]
        w = _word_of(tok)
        matched = None
        if w is not None:
            for words in _BY_FIRST.get(w, []):
                seg = raw[i:i + len(words)]
                if len(seg) == len(words) and tuple(_word_of(t) for t in seg) == words:
                    matched = words
                    break
        if matched:
            out.append(Tok("kw", " ".join(matched), tok.line))
            i += len(matched)
        else:
            if tok.kind == "word":
                tok = Tok("id", tok.value, tok.line)
            out.append(tok)
            i += 1
    return out


def analyze_line(text: str, lineno: int) -> LineInfo:
    raw = lex_line(text, lineno)
    if not raw:
        return LineInfo(lineno, text, "blank")
    cuhs = sum(1 for t in raw if t.kind == "cuh")
    yell = any(t.kind == "cuh" and t.value == "CUH" for t in raw)
    if cuhs == len(raw):
        return LineInfo(lineno, text, "bare", cuhs, yell)
    if raw[-1].kind != "cuh":
        return LineInfo(lineno, text, "skipped", cuhs, yell)
    body = list(raw)
    while body and body[-1].kind == "cuh":
        body.pop()
    return LineInfo(lineno, text, "respected", cuhs, yell, combine(body))


def analyze(source: str) -> list[LineInfo]:
    return [analyze_line(text, i) for i, text in enumerate(source.splitlines(), 1)]
