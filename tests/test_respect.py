from fractions import Fraction

from cuh.lexer import analyze
from cuh.respect import judge, report_text

CREW = """\
fam greet takes name cuh
    say it "wassup " wit name cuh
    pull up with ghost cuh
done cuh

the greeting function above, for the record

cousin crew be squad "dre", "mo", "lil t" cuh

run it back homie in crew cuh
    ayo greet homie cuh
done cuh

on cuh headcount crew is 3 cuh
i'm out cuh cuh
"""


def j(src):
    return judge(analyze(src))


def test_crew_example_math():
    r = j(CREW)
    assert (r.respected, r.skipped, r.cuhs) == (10, 1, 12)
    assert r.respect == 1
    assert r.avg == Fraction(6, 5)
    assert r.verdict == "ok"
    assert r.room == 3


def test_extra_cuh_buys_respect():
    r = j(CREW.replace("i'm out cuh cuh", "i'm out cuh"))
    assert r.respect == Fraction(21, 22)  # (10 + 0.5) / 11


def test_disrespect():
    r = j("a\nb\nsay it 1 cuh\nc\n")
    assert r.verdict == "disrespect"
    assert r.percent == 25
    assert r.message == "nah. you ain't even acknowledge me. (respect: 25%)"
    assert r.exit_code == 2


def test_spam_is_checked_first():
    r = j("a\nb\nc\nsay it 1 cuh cuh cuh cuh\n")
    assert r.verdict == "spam"
    assert r.message.startswith("why you saying cuh so much, cuh. what you want.")
    assert r.exit_code == 3


def test_spam_boundary():
    assert j("x cuh cuh\ny cuh\n").verdict == "ok"  # avg 1.5 exactly
    assert j("x cuh cuh\ny cuh cuh\nz cuh\n").verdict == "spam"  # 5/3


def test_bare_cuh_lines_count_cuhs_but_not_lines():
    r = j("say it 1 cuh\ncuh\n")
    assert (r.respected, r.skipped, r.bare, r.cuhs) == (1, 0, 1, 2)
    assert j("cuh\n").verdict == "spam"  # all cuh, no lines


def test_apologies_are_capped():
    base = "\n".join(["x cuh"] * 4 + ["comment"] * 6)
    assert j(base).verdict == "disrespect"
    r = j(base + "\nmy bad cuh\nmy bad cuh\nmy bad cuh\n")
    assert r.apologies == 3 and r.verdict == "ok" and r.warnings == []
    r = j(base + "\nmy bad cuh\n" * 4)
    assert r.warnings == ["you don't even mean that"]
    assert r.respect == j(base + "\nx cuh\nmy bad cuh\nmy bad cuh\nmy bad cuh\n").respect


def test_no_cap_costs_half_a_line():
    plain = j("x cuh\ny cuh\nz cuh\ncomment\n")
    nocap = j("no cap cuh\ny cuh\nz cuh\ncomment\n")
    assert plain.respect - nocap.respect == Fraction(1, 8)


def test_empty_file_runs():
    r = j("")
    assert r.verdict == "ok" and r.respect == 1 and r.avg is None


def test_report_text():
    text = report_text(j(CREW))
    assert "respect: 100%" in text
    assert "you got room for 3 more comments" in text
