from paste.deploy import loadwsgi
from eventlet import wsgi, listen
from eventlet.green import socket, ssl
from eventlet import sleep, GreenPool
import os
import time
import errno
from swift.common.utils import get_hub, config_true_value
import eventlet
import eventlet.debug
import inspect

class NamedConfigLoader(loadwsgi.ConfigLoader):
    """
    Patch paste.deploy's ConfigLoader so each context object will know what
    config section it came from.
    """

    def get_context(self, object_type, name=None, global_conf=None):
        context = super(NamedConfigLoader, self).get_context(
            object_type, name=name, global_conf=global_conf)
        context.name = name
        return context


loadwsgi.ConfigLoader = NamedConfigLoader

def wrap_conf_type(f):
    """
    Wrap a function whos first argument is a paste.deploy style config uri,
    such that you can pass it an un-adorned raw filesystem path (or config
    string) and the config directive (either config:, config_dir:, or
    config_str:) will be added automatically based on the type of entity
    (either a file or directory, or if no such entity on the file system -
    just a string) before passing it through to the paste.deploy function.
    """
    def wrapper(conf_path, *args, **kwargs):
        if os.path.isdir(conf_path):
            conf_type = 'config_dir'
        else:
            conf_type = 'config'
        conf_uri = '%s:%s' % (conf_type, conf_path)
        return f(conf_uri, *args, **kwargs)
    return wrapper


appconfig = wrap_conf_type(loadwsgi.appconfig)


def get_socket(conf):
    """Bind socket to bind ip:port in conf

    :param conf: Configuration dict to read settings from

    :returns : a socket object as returned from socket.listen or
               ssl.wrap_socket if conf specifies cert_file
    """
    try:
        bind_port = int(conf['bind_port'])
    except (ValueError, KeyError, TypeError):
        raise ConfigFilePortError()
    bind_addr = (conf.get('bind_ip', '0.0.0.0'), bind_port)
    address_family = [addr[0] for addr in socket.getaddrinfo(bind_addr[0], bind_addr[1], socket.AF_UNSPEC, socket.SOCK_STREAM) if addr[0] in (socket.AF_INET, socket.AF_INET6)][0]
    sock = None
    bind_timeout = int(conf.get('bind_timeout', 30))
    retry_until = time.time() + bind_timeout
    warn_ssl = False
    while not sock and time.time() < retry_until:
        try:
            sock = listen(bind_addr, backlog=int(conf.get('backlog', 4096)),
                          family=address_family)
            if 'cert_file' in conf:
                warn_ssl = True
                sock = ssl.wrap_socket(sock, certfile=conf['cert_file'],
                                       keyfile=conf['key_file'])
        except socket.error as err:
            if err.args[0] != errno.EADDRINUSE:
                raise
            sleep(0.1)
    if not sock:
        raise Exception(('Could not bind to %s:%s after trying for %s seconds') % (bind_addr[0], bind_addr[1], bind_timeout))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # in my experience, sockets can hang around forever without keepalive
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    if hasattr(socket, 'TCP_KEEPIDLE'):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 600)
    if warn_ssl:
        ssl_warning_message = ('WARNING: SSL should only be enabled for '
                                'testing purposes. Use external SSL '
                                'termination for a production deployment.')
        #get_logger(conf).warning(ssl_warning_message)
        print(ssl_warning_message)
    return sock

class RestrictedGreenPool(GreenPool):
    """
    Works the same as GreenPool, but if the size is specified as one, then the
    spawn_n() method will invoke waitall() before returning to prevent the
    caller from doing any other work (like calling accept()).
    """
    def __init__(self, size=1024):
        super(RestrictedGreenPool, self).__init__(size=size)
        self._rgp_do_wait = (size == 1)

    def spawn_n(self, *args, **kwargs):
        super(RestrictedGreenPool, self).spawn_n(*args, **kwargs)
        if self._rgp_do_wait:
            self.waitall()

class PipelineWrapper(object):
    """
    This class provides a number of utility methods for
    modifying the composition of a wsgi pipeline.
    """

    def __init__(self, context):
        self.context = context

    def __contains__(self, entry_point_name):
        try:
            self.index(entry_point_name)
            return True
        except ValueError:
            return False

    def startswith(self, entry_point_name):
        """
        Tests if the pipeline starts with the given entry point name.

        :param entry_point_name: entry point of middleware or app (Swift only)

        :returns: True if entry_point_name is first in pipeline, False
                  otherwise
        """
        try:
            first_ctx = self.context.filter_contexts[0]
        except IndexError:
            first_ctx = self.context.app_context
        return first_ctx.entry_point_name == entry_point_name

    def _format_for_display(self, ctx):
        # Contexts specified by pipeline= have .name set in NamedConfigLoader.
        if hasattr(ctx, 'name'):
            return ctx.name
        # This should not happen: a foreign context. Let's not crash.
        return "<unknown>"

    def __str__(self):
        parts = [self._format_for_display(ctx)
                 for ctx in self.context.filter_contexts]
        parts.append(self._format_for_display(self.context.app_context))
        return " ".join(parts)

    def create_filter(self, entry_point_name):
        """
        Creates a context for a filter that can subsequently be added
        to a pipeline context.

        :param entry_point_name: entry point of the middleware (Swift only)

        :returns: a filter context
        """
        spec = 'egg:swift#' + entry_point_name
        ctx = loadwsgi.loadcontext(loadwsgi.FILTER, spec,
                                   global_conf=self.context.global_conf)
        ctx.protocol = 'paste.filter_factory'
        ctx.name = entry_point_name
        return ctx

    def index(self, entry_point_name):
        """
        Returns the first index of the given entry point name in the pipeline.

        Raises ValueError if the given module is not in the pipeline.
        """
        for i, ctx in enumerate(self.context.filter_contexts):
            if ctx.entry_point_name == entry_point_name:
                return i
        raise ValueError("%s is not in pipeline" % (entry_point_name,))

    def insert_filter(self, ctx, index=0):
        """
        Inserts a filter module into the pipeline context.

        :param ctx: the context to be inserted
        :param index: (optional) index at which filter should be
                      inserted in the list of pipeline filters. Default
                      is 0, which means the start of the pipeline.
        """
        self.context.filter_contexts.insert(index, ctx)


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
    if ctx.object_type.name == 'pipeline':
        # give app the opportunity to modify the pipeline context
        app = ctx.app_context.create()
        func = getattr(app, 'modify_wsgi_pipeline', None)
        if func and allow_modify_pipeline:
            func(PipelineWrapper(ctx))
    return ctx.create()

def run_server(conf, logger, sock, global_conf=None):
    # Ensure TZ environment variable exists to avoid stat('/etc/localtime') on
    # some platforms. This locks in reported times to the timezone in which
    # the server first starts running in locations that periodically change
    # timezones.
    os.environ['TZ'] = time.strftime("%z", time.gmtime())

    wsgi.HttpProtocol.default_request_version = "HTTP/1.0"
    # Turn off logging requests by the underlying WSGI software.
    wsgi.HttpProtocol.log_request = lambda *a: None
    # Redirect logging other messages by the underlying WSGI software.
    wsgi.HttpProtocol.log_message = \
        lambda s, f, *a: logger.error('ERROR WSGI: ' + f % a)
    wsgi.WRITE_TIMEOUT = int(conf.get('client_timeout') or 60)
    print "THE PROGRAM IS IN THE RUN_SERVER"

    print "eventlet.hubs.get_default_hub(): ", eventlet.hubs.get_default_hub()
    print "eventlet.hubs.get_hub(): ", eventlet.hubs.get_hub()
    print "GET_HUB() : ", get_hub()

    eventlet.hubs.use_hub(get_hub())
    eventlet.patcher.monkey_patch(all=False, socket=True)

    eventlet_debug = config_true_value(conf.get('eventlet_debug', 'no'))
    print "eventlet_debug: ", eventlet_debug

    eventlet.debug.hub_exceptions(eventlet_debug)
    print "eventlet.debug.hub_exceptions(eventlet_debug) : ", eventlet.debug.hub_exceptions(eventlet_debug)

    app = loadapp(conf['__file__'], global_conf=global_conf)

    max_clients = int(conf.get('max_clients', '1024'))
    print "max_clients: ", max_clients
    pool = RestrictedGreenPool(size=max_clients)
    print "pool : ", pool
    try:
        # Disable capitalizing headers in Eventlet if possible.  This is
        # necessary for the AWS SDK to work with swift3 middleware.
        argspec = inspect.getargspec(wsgi.server)
        print "argspec : ", argspec
        if 'capitalize_response_headers' in argspec.args:
            wsgi.server(sock, app, custom_pool=pool,
                        capitalize_response_headers=False)
        else:
            wsgi.server(sock, app, custom_pool=pool)
    except socket.error as err:
        if err[0] != errno.EINVAL:
            raise



def run_wsgi(conf_path, app_section, *args, **kwargs):
    """
    Runs the server using the specified number of workers.

    :param conf_path: Path to paste.deploy style configuration file/directory
    :param app_section: App name from conf file to load config from
    :returns: 0 if successful, nonzero otherwise
    """
    # conf = {
    #     '__file__': conf_path
    # }

    # Load configuration, Set logger and Load request processor
    try:
        (conf, logger, log_name) = \
            _initrp(conf_path, app_section, *args, **kwargs)
    except ConfigFileError as e:
        print(e)
        return 1

    logger = None
    #sock = listen(('127.0.0.1', 8080))
    # bind to address and port
    try:
        sock = get_socket(conf)
    except ConfigFilePortError:
        msg = 'bind_port wasn\'t properly set in the config file. ' \
              'It must be explicitly set to a valid port number.'
        #logger.error(msg)
        print(msg)
        return 1
    # sock2 = listener.dup()
    global_conf = None
    run_server(conf, logger, sock, global_conf=global_conf)
    return 0

class ConfigFileError(Exception):
    pass

class ConfigFilePortError(ConfigFileError):
    pass


def _initrp(conf_path, app_section, *args, **kwargs):
    try:
        conf = appconfig(conf_path, name=app_section, relative_to="./")
    except Exception as e:
        raise ConfigFileError("Error trying to load config from %s: %s" %
                              (conf_path, e))

    return (conf, None, None)
