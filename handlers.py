import asyncio
import collections
import functools

handlers = collections.defaultdict(set)


def handle(event):
    def inner(func):
        print("wrapping", func)

        @functools.wraps(func)
        def wrapper(connection, *args):
            if asyncio.iscoroutinefunction(func):
                asyncio.run_coroutine_threadsafe(func(connection, *args), connection.loop)
            else:
                func(connection, *args)

        handlers[event].add(wrapper)
        return func

    return inner
