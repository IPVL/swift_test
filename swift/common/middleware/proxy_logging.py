from swift.inspect_custom import  whoami, whosdaddy


print __name__


class ProxyLoggingMiddleware(object):
    """docstring for ProxyLoggingMiddleware"""
    def __init__(self, app, conf):
        print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__


def filter_factory(global_conf, **local_conf):
    # print kwargs, local_conf
    print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def proxy_logger(app):
        print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return ProxyLoggingMiddleware(app, conf)
    return proxy_logger