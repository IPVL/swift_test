from swift.inspect_custom import  whoami, whosdaddy


pass  # (WIS) print __name__


class Bulk(object):
    """docstring for Bulk"""
    def __init__(self, app, conf, max_containers_per_extraction, max_failed_extractions, max_deletes_per_request, max_failed_deletes, yield_frequency, retry_count, retry_interval):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf
        self.max_containers_per_extraction = max_containers_per_extraction
        self.max_failed_extractions = max_failed_extractions
        self.max_deletes_per_request = max_deletes_per_request
        self.max_failed_deletes = max_failed_deletes
        self.yield_frequency = yield_frequency
        self.retry_count = retry_count
        self.retry_interval = retry_interval

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    max_containers_per_extraction = \
        int(conf.get('max_containers_per_extraction', 10000))
    max_failed_extractions = int(conf.get('max_failed_extractions', 1000))
    max_deletes_per_request = int(conf.get('max_deletes_per_request', 10000))
    max_failed_deletes = int(conf.get('max_failed_deletes', 1000))
    yield_frequency = int(conf.get('yield_frequency', 10))
    retry_count = int(conf.get('delete_container_retry_count', 0))
    retry_interval = 1.5

    # register_swift_info(
    #     'bulk_upload',
    #     max_containers_per_extraction=max_containers_per_extraction,
    #     max_failed_extractions=max_failed_extractions)
    # register_swift_info(
    #     'bulk_delete',
    #     max_deletes_per_request=max_deletes_per_request,
    #     max_failed_deletes=max_failed_deletes)

    def bulk_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return Bulk(
            app, conf,
            max_containers_per_extraction=max_containers_per_extraction,
            max_failed_extractions=max_failed_extractions,
            max_deletes_per_request=max_deletes_per_request,
            max_failed_deletes=max_failed_deletes,
            yield_frequency=yield_frequency,
            retry_count=retry_count,
            retry_interval=retry_interval)
    return bulk_filter
