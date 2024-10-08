import queue
from mv.data_types import DelayArgs


def test_temp():
    q = queue.Queue()
    q.put(1)
    q.put(2)
    iter = q.queue.__iter__()
    x1 = next(iter)
    x2 = next(iter)
