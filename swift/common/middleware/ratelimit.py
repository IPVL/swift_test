from swift.inspect_custom import  whoami, whosdaddy


pass  # (WIS) print __name__


class RateLimitMiddleware(object):
    """docstring for RateLimitMiddleware"""
    def __init__(self, app, conf):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    # account_ratelimit = float(conf.get('account_ratelimit', 0))
    # max_sleep_time_seconds = \
    #     float(conf.get('max_sleep_time_seconds', 60))
    # container_ratelimits, cont_limit_info = interpret_conf_limits(
    #     conf, 'container_ratelimit_', info=1)
    # container_listing_ratelimits, cont_list_limit_info = \
    #     interpret_conf_limits(conf, 'container_listing_ratelimit_', info=1)
    # # not all limits are exposed (intentionally)
    # register_swift_info('ratelimit',
    #                     account_ratelimit=account_ratelimit,
    #                     max_sleep_time_seconds=max_sleep_time_seconds,
    #                     container_ratelimits=cont_limit_info,
    #                     container_listing_ratelimits=cont_list_limit_info)

    def limit_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return RateLimitMiddleware(app, conf)

    return limit_filter
