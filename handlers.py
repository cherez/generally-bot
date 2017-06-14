import collections

handlers = collections.defaultdict(list)


def handle(event):
    def inner(func):
        handlers[event].append(func)
        return func
    return inner
