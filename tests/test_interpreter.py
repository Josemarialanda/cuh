import pytest

from helpers import ok, run

PAD = "\n".join(['cousin pad be 0 cuh'] * 8)
# two skipped lines keep respect between 75% and 90%, so errors use the stock wording
LOW = PAD + "\nthis comment lowers the mood\nso does this one\n"


def test_say_and_wit():
    assert ok('cousin name be "dre" cuh\nsay it fr "wassup " wit name cuh') == "wassup dre\n"


@pytest.mark.parametrize("src,expected", [
    ("2 plus 3", "5"),
    ("10 taxed 3", "7"),
    ("4 times 2", "8"),
    ("10 split 4", "2.5"),
    ("10 split 5", "2"),
    ("10 leftover from 3", "1"),
    ("negative 5 plus 2", "-3"),
    ("hol up 2 plus 3 aight times 4", "20"),
    ("3 is 3", "facts"),
    ('"mo" ain\'t "mo"', "cap"),
    ("2 under 3 and 3 over 2", "facts"),
    ("3 at most 3 and 3 at least 4", "cap"),
    ("nah cap", "facts"),
    ("ghost", "ghost"),
    ("1 is facts", "cap"),
    ('squad 1, "a", squad 2', 'squad 1, "a", hol up squad 2 aight'),
    ("empty squad", "empty squad"),
    ("from 3 to 1", "squad 3, 2, 1"),
    ("headcount squad 1, 2", "2"),
    ('as number "42" plus 1', "43"),
    ("as words 5 wit 5", "55"),
    ('"ha" times 3', "hahaha"),
])
def test_expressions(src, expected):
    assert ok(f"say it fr {src} cuh") == expected + "\n"


def test_variables_and_bump():
    out = ok("""
        cousin x be 1 cuh
        x switch up to 10 cuh
        run x up by 5 cuh
        run x down by 2 cuh
        say it fr x cuh
    """)
    assert out == "13\n"


def test_squads_are_one_based_and_mutable():
    out = ok("""
        cousin crew be squad "dre", "mo" cuh
        crew spot 1 switch up to "lil t" cuh
        put "big mike" in crew cuh
        kick "mo" out of crew cuh
        say it fr crew spot 1 cuh
        say it fr crew cuh
    """)
    assert out == 'lil t\nsquad "lil t", "big mike"\n'


def test_loops_break_continue():
    out = ok("""
        cousin n be 0 cuh
        long as facts cuh
            run n up by 1 cuh
            if it's n leftover from 2 is 0 cuh
                next up cuh
            done cuh
            if it's n over 5 cuh
                dip cuh
            done cuh
            say it fr n cuh
        done cuh
        run it back c in "ab" cuh
            say it fr c cuh
        done cuh
    """)
    assert out == "1\n3\n5\na\nb\n"


def test_functions_ayo_and_spite():
    src = """
        fam add takes a, b cuh
            say it fr "adding" cuh
            pull up with a plus b cuh
        done cuh
        say it fr ayo add 2, 3 cuh
        say it fr add 2, 3 cuh
    """
    assert ok(src) == "adding\n5\nadding\nghost\n"


def test_bare_name_statement_calls_with_spite():
    assert ok('fam hype cuh\nsay it fr "yuh" cuh\ndone cuh\nhype cuh') == "yuh\n"


def test_recursion_and_closures():
    out = ok("""
        fam fact takes n cuh
            if it's n at most 1 cuh
                pull up with 1 cuh
            done cuh
            pull up with n times ayo fact n taxed 1 cuh
        done cuh
        say it fr ayo fact 10 cuh
    """)
    assert out == "3628800\n"


def test_exit():
    assert ok('say it fr 1 cuh\ni\'m out cuh\nsay it fr 2 cuh') == "1\n"


def test_assert_passes():
    assert ok("on cuh 1 is 1 cuh\nsay it fr \"ok\" cuh") == "ok\n"


def test_try_binds_the_tea():
    out = ok("""
        try me cuh
            say it fr 1 split 0 cuh
        if it go left cuh
            say it fr the tea cuh
        done cuh
    """)
    assert out == "cuh you divided by zero??\n"


def test_ask_em():
    assert ok('cousin n be ask em "name? " cuh\nsay it fr "yo " wit n cuh', stdin="dre\n") == "name? yo dre\n"


def test_lowkey_goes_to_stderr():
    import io
    from cuh.interpreter import run_source
    out, err = io.StringIO(), io.StringIO()
    run_source('lowkey say it fr "psst" cuh\n', out=out, err=err)
    assert out.getvalue() == "" and err.getvalue() == "psst\n"


def test_highkey_yells():
    out = ok("""
        highkey say it fr "a" cuh
        highkey say it fr "b" cuh
        highkey say it fr "Hi, there!" cuh
    """)
    assert out == "A\nB\nhi there\n"


# mood

def test_three_yells_sulk_and_apology_fixes_it():
    out = ok("""
        say it fr "A!" CUH
        say it fr "B!" CUH
        say it fr "C!" CUH
        say it fr "D!" cuh
        my bad cuh
        say it fr "E!" cuh
    """)
    assert out == "A!\nB!\nc\nd\nE!\n"


def test_yells_in_loops_count_each_time():
    out = ok("""
        run it back i in from 1 to 3 CUH
            say it fr "Hi!" cuh
        done cuh
        run it back i in from 1 to 3 cuh
            say it fr "Hi!" CUH
        done cuh
    """)
    assert out == "Hi!\nHi!\nHi!\nHi!\nhi\nhi\n"


def test_random_cuh_is_seeded():
    src = "\n".join(['say it "yo" cuh'] * 50)
    a, b = ok(src, seed=1), ok(src, seed=1)
    assert a == b
    assert "yo cuh\n" in a
    assert ok(src) == ok(src)  # default seed comes from the file


def test_fr_and_no_cap_never_add_cuh():
    assert "cuh" not in ok("\n".join(['say it fr "yo" cuh'] * 50), seed=1)
    assert "cuh" not in ok("no cap cuh\n" + "\n".join(['say it "yo" cuh'] * 50), seed=1)


# error bank

@pytest.mark.parametrize("src,msg", [
    ("say it 1 split 0 cuh", "cuh you divided by zero??"),
    ("say it fooo cuh", 'who is "fooo" cuh, never met em'),
    ("on cuh 1 is 2 cuh", "you lied on cuh"),
    ("fam f cuh\nayo f cuh\ndone cuh\nayo f cuh", "i'm tired cuh"),
    ("say it hol up squad 1 aight plus 2 cuh", "you can't add a number to a squad cuh, be serious"),
    ("cousin x be 1 cuh\nayo x cuh", "that ain't fam"),
    ('cousin crew be squad 1, 2, 3 cuh\nsay it crew spot 4 cuh', "crew only got 3 people cuh"),
    ('cousin crew be squad 1 cuh\nkick 2 out of crew cuh', "2 ain't even in there cuh"),
    ('say it as number "abc" cuh', '"abc" ain\'t a number cuh'),
    ("fam f takes a cuh\ndone cuh\nayo f 1, 2 cuh", "f takes 1, you gave 2 cuh"),
    ('link up with "nope.cuh" cuh', 'can\'t find "nope.cuh" cuh, where it at'),
])
def test_error_bank_stock_mood(src, msg):
    code, out = run(LOW + src)
    assert code == 1
    assert out == msg + "\n"


def test_syntax_error_message():
    code, out = run(LOW + "say it 1 plus cuh")
    assert code == 1 and out == "nah cuh, line 11 ain't it\n"


def test_helpful_mood_suggests_names():
    code, out = run('cousin name be "dre" cuh\nsay it nmae cuh')
    assert out == 'line 2: never met "nmae", you mean "name"?\n'
    code, out = run("say it 1 split 0 cuh")
    assert out == "line 1: cuh you divided by zero??\n"


def test_helpful_syntax_errors_explain():
    code, out = run("cousin x 5 cuh")
    assert out == 'nah cuh, line 1 ain\'t it (expected "be" after cousin x, got "5")\n'


def test_sulking_errors_are_curt():
    code, out = run('say it fr 1 CUH\nsay it fr 2 CUH\nsay it fr 3 CUH\nsay it nmae cuh')
    assert out.endswith("line 4. figure it out.\n")


def test_refusals():
    code, out = run("comment\ncomment\nsay it 1 cuh")
    assert code == 2 and out == "nah. you ain't even acknowledge me. (respect: 33%)\n"
    code, out = run("say it 1 cuh cuh cuh")
    assert code == 3 and out.startswith("why you saying cuh so much, cuh. what you want.")


# imports

def test_imports(tmp_path):
    (tmp_path / "lib.cuh").write_text('fam hi cuh\npull up with "hi" cuh\ndone cuh\n')
    main = tmp_path / "main.cuh"
    src = 'link up with "lib.cuh" cuh\nlink up with "lib.cuh" cuh\nsay it fr ayo hi cuh\n'
    main.write_text(src)
    assert run(src, path=str(main)) == (0, "hi\n")


def test_disrespected_import(tmp_path):
    (tmp_path / "bad.cuh").write_text("a\nb\nc\nsay it 1 cuh\n")
    src = LOW + 'link up with "bad.cuh" cuh\n'
    code, out = run(src, path=str(tmp_path / "main.cuh"))
    assert code == 1 and out == "bad.cuh ain't respected, i'm not fw that\n"
