class Schedule:
    def __init__(self, delay, function):
        self.delay = delay
        self.function = function

schedules = []

def every(delay):
    def inner(function):
        s = Schedule(delay, function)
        schedules.append(s)
        return function
    return inner


