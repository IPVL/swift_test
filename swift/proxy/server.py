from swift.ipvl.inspect_custom import  whoami, whosdaddy


pass  # (WIS) print __name__

required_filters = [
    {'name': 'catch_errors'},
    {'name': 'gatekeeper',
     'after_fn': lambda pipe: (['catch_errors']
                               if pipe.startswith('catch_errors')
                               else [])},
    {'name': 'dlo', 'after_fn': lambda _junk: [
        'staticweb', 'tempauth', 'keystoneauth',
        'catch_errors', 'gatekeeper', 'proxy_logging']}]


class Application(object):
    """docstring for Application"""
    def __init__(self, arg=None):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.arg = arg

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return self.__class__.__name__

    def modify_wsgi_pipeline(self, pipe):
        """
        Called during WSGI pipeline creation. Modifies the WSGI pipeline
        context to ensure that mandatory middleware is present in the pipeline.

        :param pipe: A PipelineWrapper object
        """
        pipeline_was_modified = False
        print 'pipe: %s ' % pipe
        for filter_spec in reversed(required_filters):
            filter_name = filter_spec['name']
            print 'filter name : %s ' % filter_name
            if filter_name not in pipe:
                afters = filter_spec.get('after_fn', lambda _junk: [])(pipe)
                print '%s after : %s ' % (filter_name, afters)
                insert_at = 0
                for after in afters:
                    try:
                        insert_at = max(insert_at, pipe.index(after) + 1)
                    except ValueError:  # not in pipeline; ignore it
                        pass
                # self.logger.info(
                #     'Adding required filter %s to pipeline at position %d' %
                #     (filter_name, insert_at))
                print 'Adding required filter %s to pipeline at position %d' % (filter_name, insert_at)
                ctx = pipe.create_filter(filter_name)
                pipe.insert_filter(ctx, index=insert_at)
                pipeline_was_modified = True

        if pipeline_was_modified:
            # self.logger.info("Pipeline was modified. New pipeline is \"%s\".",
            #                  pipe)
            print "Pipeline was modified. New pipeline is \"%s\".", pipe
        else:
            # self.logger.debug("Pipeline is \"%s\"", pipe)
            print "Pipeline is \"%s\"", pipe


def app_factory(global_conf, **local_conf):
    """paste.deploy app factory for creating WSGI proxy apps."""
    print global_conf
    print local_conf
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)
    app = Application(conf)
    # app.check_config()
    return app
