"""AST nodes. Every node remembers its source line for error messages."""

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int


# expressions

@dataclass
class Num(Node):
    value: int | float


@dataclass
class Str(Node):
    value: str


@dataclass
class Lit(Node):
    value: object  # True, False, None


@dataclass
class Var(Node):
    name: str


@dataclass
class Squad(Node):
    items: list


@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Unary(Node):
    op: str
    operand: Node


@dataclass
class Index(Node):
    target: Node
    index: Node


@dataclass
class Range(Node):
    start: Node
    end: Node


@dataclass
class Call(Node):
    name: str
    args: list
    ayo: bool


# statements

@dataclass
class Stmt(Node):
    yell: bool = field(default=False, kw_only=True)


@dataclass
class Declare(Stmt):
    name: str
    value: Node


@dataclass
class Assign(Stmt):
    target: Node  # Var or Index
    value: Node


@dataclass
class Bump(Stmt):
    name: str
    amount: Node
    sign: int


@dataclass
class Say(Stmt):
    value: Node
    fr: bool
    mode: str  # normal, lowkey, highkey


@dataclass
class FamDef(Stmt):
    name: str
    params: list
    body: list


@dataclass
class Return(Stmt):
    value: Node | None


@dataclass
class ExprStmt(Stmt):
    expr: Node


@dataclass
class If(Stmt):
    branches: list  # [(cond, body)]
    otherwise: list | None


@dataclass
class ForEach(Stmt):
    name: str
    iterable: Node
    body: list


@dataclass
class While(Stmt):
    cond: Node
    body: list


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


@dataclass
class Assert(Stmt):
    cond: Node


@dataclass
class Try(Stmt):
    body: list
    handler: list


@dataclass
class Put(Stmt):
    item: Node
    target: Node


@dataclass
class Kick(Stmt):
    item: Node
    target: Node


@dataclass
class Link(Stmt):
    path: str


@dataclass
class NoCap(Stmt):
    pass


@dataclass
class Apology(Stmt):
    pass


@dataclass
class Exit(Stmt):
    pass
