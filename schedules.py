import asyncio
import functools


class Schedule:
    def __init__(self, delay, function):
        self.delay = delay
        self.function = function


schedules = []


def every(delay):
    def inner(function):
        @functools.wraps(function)
        def wrapper(connection):
            if asyncio.iscoroutinefunction(function):
                return asyncio.run_coroutine_threadsafe(function(connection), connection.loop)
            else:
                return function(connection)
        s = Schedule(delay, wrapper)
        schedules.append(s)
        return function

    return inner
