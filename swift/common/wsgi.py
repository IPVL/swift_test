from paste.deploy import loadwsgi
from eventlet import wsgi, listen


def loadcontext(object_type, uri, name=None, relative_to=None,
                global_conf=None):
    conf_file = uri
    relative_to = '.'
    return loadwsgi.loadcontext(loadwsgi.APP, 'config:'+conf_file, name=name, relative_to=relative_to, global_conf=global_conf)


def loadapp(conf_file, global_conf=None, allow_modify_pipeline=True):
    """
    Loads a context from a config file, and if the context is a pipeline
    then presents the app with the opportunity to modify the pipeline.
    """
    global_conf = global_conf or {}
    ctx = loadcontext(loadwsgi.APP, conf_file, global_conf=global_conf)
    # if ctx.object_type.name == 'pipeline':
    #     # give app the opportunity to modify the pipeline context
    #     app = ctx.app_context.create()
    #     func = getattr(app, 'modify_wsgi_pipeline', None)
    #     if func and allow_modify_pipeline:
    #         func(PipelineWrapper(ctx))
    return ctx.create()


def run_server(conf, logger, sock, global_conf=None):
    app = loadapp(conf['__file__'], global_conf=global_conf)
    wsgi.server(sock=sock, site=app)


def run_wsgi(conf_path, app_section, *args, **kwargs):
    """
    Runs the server using the specified number of workers.

    :param conf_path: Path to paste.deploy style configuration file/directory
    :param app_section: App name from conf file to load config from
    :returns: 0 if successful, nonzero otherwise
    """
    conf = {
        '__file__': conf_path
    }

    logger = None
    sock = listen(('127.0.0.1', 8080))
    # sock2 = listener.dup()
    global_conf = None
    run_server(conf, logger, sock, global_conf=global_conf)
    return 0
