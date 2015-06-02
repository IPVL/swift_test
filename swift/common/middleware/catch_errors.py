from swift.inspect_custom import  whoami, whosdaddy


print __name__


class CatchErrorMiddleware(object):
    """docstring for CatchErrorMiddleware"""
    def __init__(self, app, conf):
        print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return CatchErrorMiddleware(app, conf)
    return except_filter
