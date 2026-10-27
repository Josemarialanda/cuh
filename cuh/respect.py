"""The respect check: a pure function over line stats, run before parsing."""

import math
from dataclasses import dataclass, field
from fractions import Fraction

THRESHOLD = Fraction(3, 4)
SPAM_LIMIT = Fraction(3, 2)
APOLOGY_CREDIT = Fraction(3, 2)
MAX_APOLOGIES = 3
NOCAP_COST = Fraction(1, 2)

DISRESPECT = 2
SPAM = 3


@dataclass
class RespectReport:
    respected: int
    skipped: int
    bare: int
    cuhs: int
    apologies: int
    nocap: bool
    respect: Fraction
    avg: Fraction | None  # None when there are no cuhs at all
    verdict: str  # ok, disrespect, spam
    room: int
    warnings: list[str] = field(default_factory=list)

    @property
    def percent(self) -> int:
        return math.floor(self.respect * 100)

    @property
    def avg_text(self) -> str:
        if self.avg is None:
            return "0"
        if self.avg == math.inf:
            return "infinity"
        return f"{float(self.avg):.2f}".rstrip("0").rstrip(".")

    @property
    def message(self) -> str:
        if self.verdict == "spam":
            return f"why you saying cuh so much, cuh. what you want. (avg: {self.avg_text} cuh per line)"
        if self.verdict == "disrespect":
            return f"nah. you ain't even acknowledge me. (respect: {self.percent}%)"
        return ""

    @property
    def exit_code(self) -> int:
        return {"ok": 0, "disrespect": DISRESPECT, "spam": SPAM}[self.verdict]


def judge(lines) -> RespectReport:
    n = sum(1 for l in lines if l.status == "respected")
    c = sum(1 for l in lines if l.status == "skipped")
    bare = sum(1 for l in lines if l.status == "bare")
    t = sum(l.cuhs for l in lines if l.status in ("respected", "bare"))
    apologies = sum(1 for l in lines if l.status == "respected" and l.is_apology)
    nocap = any(l.status == "respected" and l.is_nocap for l in lines)

    extra = t - n
    credit = n + Fraction(extra, 2) + APOLOGY_CREDIT * min(apologies, MAX_APOLOGIES)
    if nocap:
        credit -= NOCAP_COST
    total = n + c
    respect = Fraction(1) if total == 0 else max(Fraction(0), min(Fraction(1), credit / total))

    if n:
        avg = Fraction(t, n)
    else:
        avg = math.inf if t else None

    if avg is not None and avg > SPAM_LIMIT:
        verdict = "spam"
    elif respect < THRESHOLD:
        verdict = "disrespect"
    else:
        verdict = "ok"

    room = max(0, math.floor(credit / THRESHOLD - total)) if verdict == "ok" else 0
    warnings = ["you don't even mean that"] if apologies > MAX_APOLOGIES else []
    return RespectReport(n, c, bare, t, apologies, nocap, respect, avg, verdict, room, warnings)


def report_text(r: RespectReport) -> str:
    lines = [
        f"lines: {r.respected} respected, {r.skipped} skipped, {r.bare} bare",
        f"cuhs: {r.cuhs} (avg {r.avg_text} per line)",
        f"respect: {r.percent}%",
    ]
    if r.apologies:
        lines.append(f"apologies: {r.apologies}" + (" (only 3 count)" if r.apologies > MAX_APOLOGIES else ""))
    if r.verdict == "ok":
        if r.room == 0:
            room = "no more room for comments, don't push it"
        elif r.room == 1:
            room = "you got room for 1 more comment"
        else:
            room = f"you got room for {r.room} more comments"
        lines.append(f"verdict: we good. {room}")
    else:
        lines.append(f"verdict: {r.message}")
    return "\n".join(lines)
