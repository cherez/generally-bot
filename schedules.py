class Schedule:
    def __init__(self, delay, function):
        self.delay = delay
        self.function = function

    def run(self, timer, connection):
        self.function(connection)
        timer.enter(self.delay, 0, self.run, [timer, connection])

schedules = []

def every(delay):
    def inner(function):
        s = Schedule(delay, function)
        schedules.append(s)
        return function
    return inner


