import asyncio
import collections
import functools

handlers = collections.defaultdict(set)


def handle(event):
    def inner(func):
        @functools.wraps(func)
        def wrapper(connection, *args):
            connection.run_action(func(connection, *args))

        handlers[event].add(wrapper)
        return func

    return inner
