# cuh

An esoteric programming language where **every statement must end with `cuh`**.

```
say it "wassup" cuh       <- runs
say it "wassup"           <- silently skipped
```

A line without `cuh` doesn't run, so there's no comment syntax. You just don't acknowledge the line. But skipped lines cost respect, and if you disrespect the interpreter too much, it won't run your program at all.

## Quick start

Development happens inside a Nix flake:

```sh
nix develop                 # Python 3.13 + pytest, `cuh` alias
cuh examples/crew.cuh       # run a program
cuh check examples/crew.cuh # respect report
cuh                         # REPL
python -m pytest            # tests
```

Without entering the shell:

```sh
nix run . -- examples/fizzbuzz.cuh
nix build                   # builds ./result/bin/cuh (runs the tests too)
nix flake check
```

Plain Python 3.11+ works too: `python -m cuh FILE`. There are no dependencies.

## A program

```
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
```

## The respect check

Before anything runs, the interpreter reads the whole file and counts. Every non-blank line is one of:

- **respected**: the last token is `cuh` (or `CUH`)
- **skipped**: anything else. This is a comment line.
- **bare**: nothing but `cuh`s. It adds cuhs but isn't a line.

A `cuh` inside a string never counts. A `cuh` anywhere else does, including the one in `on cuh`. Swearing on cuh costs you.

```
N = respected lines   C = skipped lines   T = total cuhs
E = T - N             extra cuhs
A = 1.5 × apologies   (only the first 3 count)

respect = (N + 0.5·E + A) / (N + C)     capped at 100%
avg     = T / N
```

| condition | result | exit |
|---|---|---|
| `avg > 1.5` | `why you saying cuh so much, cuh. what you want.` | 3 |
| `respect < 75%` | `nah. you ain't even acknowledge me. (respect: 61%)` | 2 |
| otherwise | runs | 0 |

Extra cuhs buy room for comments, but only up to the spam cap. With no extra cuhs you can afford about one comment for every three statements. Maxing out the extras gets you about two for every three. `cuh check` tells you how much room you have left.

> **Gotcha:** a comment that happens to end with the word "cuh" is a statement. The interpreter will try to run it.

## Vocabulary

No symbols, just talk. The only punctuation is what normal writing uses: quotes, commas, decimal points, and apostrophes inside words. Indentation is ignored. Blocks end with `done cuh`.

### Statements

| what | how |
|---|---|
| declare | `cousin x be 5 cuh` |
| reassign | `x switch up to 6 cuh`, `crew spot 1 switch up to "dre" cuh` |
| add / subtract in place | `run x up by 2 cuh`, `run x down by 1 cuh` |
| print | `say it x cuh` |
| print exactly | `say it fr x cuh` |
| print to stderr | `lowkey say it x cuh` |
| print in caps (a yell) | `highkey say it x cuh` |
| function | `fam greet takes name cuh` … `done cuh` (also `takes a, b`, or no `takes`) |
| return | `pull up with x cuh` |
| call | `ayo greet "dre" cuh`, `ayo add 2, 3 cuh` |
| if | `if it's c cuh` … `or if it's c cuh` … `nah then cuh` … `done cuh` |
| for each | `run it back x in xs cuh` … `done cuh` |
| while | `long as c cuh` … `done cuh` |
| break / continue | `dip cuh`, `next up cuh` |
| assert | `on cuh c cuh` |
| try / catch | `try me cuh` … `if it go left cuh` … `done cuh` (the error is in `the tea`) |
| list add / remove | `put x in crew cuh`, `kick x out of crew cuh` |
| import | `link up with "lib/utils.cuh" cuh` |
| strict file | `no cap cuh` (first line only; makes every `say it` exact; costs half a line of respect) |
| apologize | `my bad cuh` |
| exit | `i'm out cuh` |

### Operators

| symbol | cuh | example |
|---|---|---|
| `+` | `plus` | `2 plus 3` |
| string `+` | `wit` | `"wassup " wit name` |
| `-` | `taxed` | `10 taxed 3` |
| `*` | `times` | `4 times 2`, `"ha" times 3` |
| `/` | `split` | `10 split 4` gives 2.5 |
| `%` | `leftover from` | `10 leftover from 3` gives 1 |
| unary `-` | `negative` | `negative 5` |
| `==` / `!=` | `is` / `ain't` | `name ain't "mo"` |
| `<` `>` `<=` `>=` | `under` `over` `at most` `at least` | `score at least 90` |
| `&&` `\|\|` `!` | `and` `or` `nah` | `nah ready and hungry` |
| `( )` | `hol up` … `aight` | `hol up 2 plus 3 aight times 4` |
| `xs[i]` | `xs spot i` | `crew spot 1` (counting starts at 1) |
| `[a, b]` | `squad a, b` / `empty squad` | `squad "dre", "mo"` |

Precedence, loosest first: `or`, `and`, `nah`, comparisons, `plus taxed wit`, `times split leftover from`, prefix words, `spot`.

Calls, `squad`, and `ayo` take **everything to the end of the line** as their arguments. Wrap them in `hol up … aight` to stop early:

```
say it ayo add 1, 2 wit "!" cuh               <- add gets (1, 2 wit "!")
say it hol up ayo add 1, 2 aight wit "!" cuh  <- "3!"
```

### Values and builtins

- numbers, `"words"`, `facts` / `cap`, `ghost` (null), squads, fams
- `headcount x`: length
- `from 1 to 10`: inclusive range (also counts down)
- `ask em "prompt"`: read a line
- `as words x`: convert to a string
- `as number x`: convert to a number

Builtins don't need `ayo`.

## Mood

**Spite.** Calling your own `fam` without `ayo` still runs it, but you get `ghost` back.

```
cousin a be ayo double 21 cuh    <- 42
cousin b be double 21 cuh        <- ghost
```

**`fr`.** Without `fr`, about 1 in 10 `say it`s adds its own ` cuh` to the output. The randomness is seeded from a hash of your file, so the same program always prints the same thing. Use `--seed N` to change the vibe.

**Yelling.** `CUH` in caps is a yell, and so is `highkey`. Yells are counted as they run, so yelling inside a loop adds up. Three yells and it starts sulking: output comes out lowercase with no punctuation. Each `my bad cuh` that runs takes one yell back.

**Error messages depend on respect:**

| mood | example |
|---|---|
| respect ≥ 90% | `line 7: never met "nmae", you mean "name"?` |
| 75–90% | `who is "nmae" cuh, never met em` |
| sulking | `line 7. figure it out.` |

The error bank:

- `nah cuh, line 12 ain't it` (syntax)
- `cuh you divided by zero??`
- `who is "fooo" cuh, never met em`
- `you lied on cuh` (failed `on cuh`)
- `i'm tired cuh` (more than 500 nested calls)
- `you can't add words to a number cuh, be serious`
- `that ain't fam` (calling something that isn't a function)
- `crew only got 3 people cuh` (bad `spot`)
- `utils.cuh ain't respected, i'm not fw that` (an import that fails its own respect check)

Runtime errors exit with code 1.

## REPL

```
$ cuh
cuh(100%)> 2 plus 3 cuh
5
cuh(100%)> hello?
...?
cuh(50%)>
```

The prompt shows respect over your last 20 lines. After the first few lines, dropping below 75% ends the session with `i'm out.`. Blocks continue on a `...>` prompt until `done cuh`.

## Examples

See `examples/`. Each `.cuh` file has a matching `.out` file with its exact output, and the test suite checks every one.

## Layout

```
cuh/lexer.py        tokens, multi-word keywords, per-line cuh counts
cuh/respect.py      the respect check
cuh/parser.py       recursive descent -> cuh/nodes.py
cuh/interpreter.py  evaluator, mood, imports
cuh/errors.py       the error bank
cuh/repl.py         REPL
cuh/__main__.py     CLI
```
