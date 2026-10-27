"""Errors and the mood-dependent message bank."""


class CuhError(Exception):
    """A cuh error. `msg` is the stock wording; `helpful` is the high-respect wording."""

    def __init__(self, msg: str, line: int, helpful: str | None = None, hint: str | None = None):
        super().__init__(msg)
        self.msg = msg
        self.line = line
        self.helpful = helpful
        self.hint = hint

    def render(self, mood: str) -> str:
        if mood == "sulk":
            return f"line {self.line}. figure it out."
        if mood == "helpful":
            text = self.helpful or f"line {self.line}: {self.msg}"
            return f"{text} ({self.hint})" if self.hint else text
        return self.msg


def syntax(line: int, hint: str | None = None) -> CuhError:
    msg = f"nah cuh, line {line} ain't it"
    return CuhError(msg, line, helpful=msg, hint=hint)


def zero(line):
    return CuhError("cuh you divided by zero??", line)


def undefined(name, line, guess=None):
    helpful = f'line {line}: never met "{name}", you mean "{guess}"?' if guess else None
    return CuhError(f'who is "{name}" cuh, never met em', line, helpful=helpful)


def lied(line):
    return CuhError("you lied on cuh", line)


def tired(line):
    return CuhError("i'm tired cuh", line)


def type_error(verb, a, prep, b, line):
    what = " ".join(p for p in (verb, a, prep, b) if p)
    return CuhError(f"you can't {what} cuh, be serious", line)


def not_fam(what, line):
    return CuhError("that ain't fam", line, helpful=f'line {line}: "{what}" ain\'t fam')


def arity(name, want, got, line):
    return CuhError(f"{name} takes {want}, you gave {got} cuh", line)


def out_of_range(who, size, unit, line):
    return CuhError(f"{who} only got {size} {unit} cuh", line)


def disrespected_import(path, line):
    return CuhError(f"{path} ain't respected, i'm not fw that", line)


def missing_import(path, line):
    return CuhError(f'can\'t find "{path}" cuh, where it at', line)


def not_a_number(text, line):
    return CuhError(f'"{text}" ain\'t a number cuh', line)


def not_in(what, line):
    return CuhError(f"{what} ain't even in there cuh", line)
