import asyncio
import random
from collections import namedtuple

from commands import command, takes, mod_only
from handlers import handle
import modules

import ast
import operator as op
import functools
import re


def limit(max_=None):
    """Return decorator that limits allowed returned values."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            try:
                mag = abs(ret)
            except TypeError:
                pass  # not applicable
            else:
                if mag > max_:
                    raise ValueError(ret)
            return ret

        return wrapper

    return decorator

def pow(base, exponent):
    if exponent > 20:
        raise ValueError('The power it too great!')
    return base**exponent

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


@limit(10 ** 50)
def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)


def eval_(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)


def roll_dice(string):
    expression = re.compile('(\d+)d(\d+)')
    while True:
        match = expression.search(string)
        if not match:
            return string
        dice = int(match[1])
        if dice > 1000:
            raise ValueError("Too many dice!")
        size = int(match[2])
        result = sum(random.randint(1, size) for i in range(dice))

        string = string.replace(match[0], str(result), 1)


@command
def roll(connection, event, body):
    string = body.strip()
    try:
        string = roll_dice(string)
        print(string)
        result = eval_expr(string)
        return str(result)
    except Exception as e:
        print(e)
        return "Invalid roll"