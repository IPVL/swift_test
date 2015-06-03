from swift.inspect_custom import  whoami, whosdaddy


pass  # (WIS) print __name__


class DynamicLargeObject(object):
    """docstring for DynamicLargeObject"""
    def __init__(self, app, conf):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__


def filter_factory(global_conf, **local_conf):
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def dlo_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return DynamicLargeObject(app, conf)
    return dlo_filter
