from subprocess import run
import re

operators = [
    "+$a",
    "-$a",
    "$a = $b",
    "$a + $b",
    "$a - $b",
    "$a * $b",
    "$a / $b",
    "$a % $b",
    "$a ** 2",
    "$a += $b",
    "$a -= $b",
    "$a *= $b",
    "$a /= $b",
    "$a %= $b",
    "$a **= $b",
    "$a &= $b",
    "$a |= $b",
    "$a ^= $b",
    "$a <<= $b",
    "$a >>= $b",
    "$a .= $b",
    "$a ??= $b",
    "$a & $b",
    "$a | $b",
    "$a ^ $b",
    "~ $a",
    "$a << $b",
    "$a >> $b",
    "$a == $b",
    "$a === $b",
    "$a != $b",
    "$a <> $b",
    "$a !== $b",
    "$a < $b",
    "$a > $b",
    "$a <= $b",
    "$a >= $b",
    "$a <=> $b",
    "++$a",
    "$a++",
    "--$a",
    "$a--",
    "$a and $b",
    "$a or $b",
    "$a xor $b",
    "! $a",
    "$a && $b",
    "$a || $b",
    "$a instanceof stdClass",
    "$a . $b",
    "print $a",
    "yield $a",
    "yield from $a",
    "$a ? $b : -1",
    "$a ? -1 : $b",
    "$a ?? $b",
    "clone $a",
    "new $a",
    "(bool)$a",
    "@$a",
]

assignment = [
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "**=",
    "&=",
    "|=",
    "^=",
    "<<=",
    ">>=",
    ".=",
    "??=",
]

def run_php(statement, a, b, c):
    cmd = f'$a = {a}; $b = {b}; $c = {c}; echo {statement}; echo "\n"; echo $a;'
    proc = run(["php", "-r", cmd], capture_output=True)
    return proc.stdout

def find_correct(statement, parens):
    if parens is None:
        return None
    
    for a, b, c in [(0, 1, 2), (1, 5, 7), (101, 256, 2), (17, 29, 3), (1.0001, 2, 1.0002), (1237, 349525, 1231)]:
        correct = run_php(statement, a, b, c)
        p0 = run_php(parens[0], a, b, c)
        p1 = run_php(parens[1], a, b, c)

        if (p0 == correct and p1 != correct):
            return parens[0]
        if (p1 == correct and p0 != correct):
            return parens[1]
    return None    

def get_parens(statement):
    try:
        a = statement.index("$a")
        b = statement.index("$b")
        c = statement.index("$c")
    except ValueError:
        return None
    
    assert a == 0
    assert c < b

    p1 = "(" + statement[:c+2] + ")" + statement[c+2:]
    p2 = statement[:c] + "(" + statement[c:] + ")"
    return [p1, p2]


def remove_parenthesized_expression(tree):
    start = tree.index("(parenthesized_expression")
    braces = 0
    for index, ch in enumerate(tree[start:]):
        if ch == "(":
            braces += 1
        if ch == ")":
            braces -= 1
            if braces == 0:
                break
    end = start + index
    skip = len("(parenthesized_expression")
    return tree[0:start] + tree[start + skip:end] + tree[end+1:]


def correct_tree(paren):
    fname = "test2.php"
    with open(fname, "w") as fp:
        fp.write("<?php\n")
        fp.write(paren)
        fp.write(";")
    proc = run(["tree-sitter", "parse", fname], capture_output=True)
    tree = proc.stdout.decode()
    tree = re.sub(r" \[.*\]", "", tree)
    tree = re.sub(r"\w+: ", "", tree)
    tree = remove_parenthesized_expression(tree)
    return tree


def combine_operators(x, y):
    y = y.replace("$a", "$c")
    to_replace = "$a"
    if "$b" in x:
        to_replace = "$b"
    
    stmt = x.replace(to_replace, y)
    p1 = x.replace(to_replace, "(" + y + ")")
    p2 = "(" + x.replace(to_replace, y.replace("$c", "$c)"))
    return stmt, [p1, p2]


if True:
    i = 0
    for x in operators:
        if "$b" in x:
            for y in operators:
                statement, parens = combine_operators(x, y)
                # parens = get_parens(statement)
                correct = find_correct(statement, parens)
                if correct is not None:
                    print("==========================")
                    print("Test", i)
                    i += 1
                    print("==========================")
                    print()
                    print("<?php")
                    print(statement,";")
                    print()
                    print("---")
                    print()
                    print(correct_tree(correct))
