from swift.ipvl.inspect_custom import whoami, whosdaddy


pass  # (WIS) print __name__


class StaticLargeObject(object):
    """docstring for StaticLargeObject"""
    def __init__(self, app, conf):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__ + "  ->  " + self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    # max_manifest_segments = int(conf.get('max_manifest_segments',
    #                                      DEFAULT_MAX_MANIFEST_SEGMENTS))
    # max_manifest_size = int(conf.get('max_manifest_size',
    #                                  DEFAULT_MAX_MANIFEST_SIZE))
    # min_segment_size = int(conf.get('min_segment_size',
    #                                 DEFAULT_MIN_SEGMENT_SIZE))
    #
    # register_swift_info('slo',
    #                     max_manifest_segments=max_manifest_segments,
    #                     max_manifest_size=max_manifest_size,
    #                     min_segment_size=min_segment_size)

    def slo_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return StaticLargeObject(app, conf)
    return slo_filter
