from swift.ipvl.inspect_custom import whoami, whosdaddy
import pprint


pass  # (WIS) print __name__
pp = pprint.PrettyPrinter(indent=3)


class CatchErrorMiddleware(object):
    """docstring for CatchErrorMiddleware"""
    def __init__(self, app, conf):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        pp.pprint(env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__ + "  ->  " + self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    print global_conf
    print local_conf
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return CatchErrorMiddleware(app, conf)
    return except_filter
