# work around modules with the same name
from __future__ import absolute_import

from datetime import datetime
from debug_toolbar.panels import DebugPanel
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

class Calls:
    def __init__(self):
        self.reset()

    def reset(self):
        self._calls = []

    def append(self, call):
        self._calls.append(call)

    def calls(self):
        return self._calls

    def size(self):
        return len(self._calls)

    def last(self):
        return self._calls[-1]

# NOTE this is not even close to thread-safe/aware
instance = Calls()

def record(func):
    def recorder(*args, **kwargs):
        call = {'function': func.__name__, 'args': None, 'exception': False}
        instance.append(call)
        # the try here is just being extra safe, it should not happen
        try:
            a = None
            # first arg is self, do we have another
            if len(args) > 1:
                a = args[1]
                # is it a dictionary (most likely multi)
                if isinstance(a, dict):
                    # just use it's keys
                    a = a.keys()
            # store the args
            call['args'] = a
        except e:
            logger.exception('tracking of call args failed')
        ret = None
        try:
            # the clock starts now
            call['start'] = datetime.now()
            ret = func(*args, **kwargs)
        except Exception as e:
            call['exception'] = e
            raise
        finally:
            # the clock stops now
            dur = datetime.now() - call['start']
            call['duration'] = (dur.seconds * 1000) + (dur.microseconds / 1000.0)
        return ret
    return recorder


class BasePanel(DebugPanel):
    name = 'Memcache'
    has_content = True

    def process_request(self, request):
        instance.reset()

    def nav_title(self):
        return 'Memcache'

    def nav_subtitle(self):
        duration = 0
        calls = instance.calls()
        for call in calls:
            duration += call['duration']
        n = len(calls)
        if (n > 0):
            return "%d calls, %0.2fms" % (n, duration)
        else:
            return "0 calls"

    def title(self):
        return 'Memcache Calls'

    def url(self):
        return ''

    def content(self):
        duration = 0
        calls = instance.calls()
        for call in calls:
            duration += call['duration']

        context = self.context.copy()
        context.update({
            'calls': calls,
            'count': len(calls),
            'duration': duration,
        })

        return render_to_string('memcache_toolbar/panels/memcache.html',
                context)
