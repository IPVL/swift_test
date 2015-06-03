from paste.deploy import loadwsgi
import logging


class WSGILog(object):

    def __init__(self):
        self.log = logging.getLogger("eventlet.wsgi")

    def write(self, string):
        self.log.debug(string.rstrip("\n"))


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


def loadapp(conf_file, global_conf=None, relative_to='.', name=None, allow_modify_pipeline=True):
    """
    Loads a context from a config file, and if the context is a pipeline
    then presents the app with the opportunity to modify the pipeline.
    """
    global_conf = global_conf or {}
    ctx = loadwsgi.loadcontext(loadwsgi.APP, conf_file, name=name, relative_to=relative_to, global_conf=global_conf)
    # if ctx.object_type.name == 'pipeline':
    #     # give app the opportunity to modify the pipeline context
    #     app = ctx.app_context.create()
    #     func = getattr(app, 'modify_wsgi_pipeline', None)
    #     if func and allow_modify_pipeline:
    #         func(PipelineWrapper(ctx))
    return ctx.create()

if __name__ == '__main__':

    from eventlet import wsgi, listen

    listener = listen(('127.0.0.1', 8080))
    sock2 = listener.dup()
    app = loadapp('config:proxy-server.conf', relative_to='.')
    wsgi.server(sock=sock2, site=app)
