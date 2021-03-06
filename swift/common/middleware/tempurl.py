from swift.ipvl.inspect_custom import whoami, whosdaddy


pass  # (WIS) print __name__


class TempURL(object):
    """docstring for TempURL"""
    def __init__(self, app, conf, methods):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf
        self.methods = methods

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__ + "  ->  " + self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    methods = conf.get('methods', 'GET HEAD PUT POST DELETE').split()
    # register_swift_info('tempurl', methods=methods)

    return lambda app: TempURL(app, conf, methods=methods)
