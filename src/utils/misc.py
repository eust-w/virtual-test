import functools
import time
from error import ZTestError


class ZTestTimeoutError(ZTestError):
    def __init__(self, timeout, cause=None):
        self.timeout = timeout
        self.cause = cause

    def __str__(self):
        if not self.cause:
            return 'timeout after %s seconds' % self.timeout
        else:
            return 'timeout after %s seconds, %s' % (self.timeout, self.cause)


def retry(time_out=5, check_interval=1):
    def wrap(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            expired = time.time() + time_out
            while True:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if time.time() < expired:
                        time.sleep(check_interval)
                    else:
                        raise ZTestTimeoutError(time_out, e)

        return inner
    return wrap

