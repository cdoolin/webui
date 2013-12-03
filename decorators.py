import gevent


def gthread(func):
    def gfunc(*args, **kwargs):
        gevent.spawn(func, *args, **kwargs)
    gfunc.__name__ = func.__name__

    return gfunc

class every(gevent.Greenlet):
    def __init__(self, time):
        gevent.Greenlet.__init__(self)

        self.time = time
        self.func = None

    def _run(self):
        while True:
            gevent.sleep(self.time)
            self.func()

    def __call__(self, func):
        self.__name__ = func.__name__
        self.func = func
        self.start()
        return func


actions = {}
def action(func):
    global actions
    actions[func.__name__] = func
    return func
