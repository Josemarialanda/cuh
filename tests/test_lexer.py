from cuh.lexer import analyze, analyze_line


def kinds(tokens):
    return [(t.kind, t.value) for t in tokens]


def test_respected_line_strips_trailing_cuhs():
    info = analyze_line('say it "wassup" cuh cuh', 1)
    assert info.status == "respected"
    assert info.cuhs == 2
    assert kinds(info.tokens) == [("kw", "say it"), ("str", "wassup")]


def test_line_without_cuh_is_skipped():
    assert analyze_line('say it "wassup"', 1).status == "skipped"


def test_cuh_inside_string_does_not_count_or_terminate():
    info = analyze_line('say it "cuh"', 1)
    assert info.status == "skipped"
    assert info.cuhs == 0


def test_text_after_cuh_means_skipped():
    assert analyze_line('say it "hi" cuh deadass this runs', 1).status == "skipped"


def test_bare_and_blank():
    assert analyze_line("cuh cuh", 1).status == "bare"
    assert analyze_line("   ", 1).status == "blank"


def test_weird_casing_is_not_a_terminator():
    assert analyze_line('say it "hi" Cuh', 1).status == "skipped"
    assert analyze_line('say it "hi" cUh', 1).status == "skipped"


def test_yell():
    info = analyze_line('say it "hi" CUH', 1)
    assert info.status == "respected" and info.yell


def test_multi_word_keywords_longest_match():
    info = analyze_line("or if it's x at least 3 cuh", 1)
    assert kinds(info.tokens) == [("kw", "or if it's"), ("id", "x"), ("kw", "at least"), ("num", 3)]
    info = analyze_line("run it back x in crew cuh", 1)
    assert info.tokens[0].value == "run it back"


def test_on_cuh_counts_its_cuh():
    info = analyze_line("on cuh x is 3 cuh", 1)
    assert info.cuhs == 2
    assert info.tokens[0].value == "on cuh"


def test_curly_apostrophes_are_normalized():
    info = analyze_line("i’m out cuh", 1)
    assert info.tokens[0].value == "i'm out"


def test_numbers_and_escapes():
    info = analyze_line('say it "a\\"b" wit 2.5 cuh', 1)
    assert kinds(info.tokens)[1:] == [("str", 'a"b'), ("kw", "wit"), ("num", 2.5)]


def test_analyze_numbers_lines():
    lines = analyze("a\n\nb cuh\n")
    assert [l.lineno for l in lines] == [1, 2, 3]
    assert [l.status for l in lines] == ["skipped", "blank", "respected"]
