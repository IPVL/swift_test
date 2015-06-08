from swift.ipvl.inspect_custom import whoami, whosdaddy
from swift.common.utils import generate_trans_id
from swift.common.wsgi import WSGIContext
from swift.common.swob import HTTPServerError
pass  # (WIS) print __name__

class CatchErrorsContext(WSGIContext):
    def __init__(self,app,trans_id_suffix=''):
        super(CatchErrorsContext,self).__init__(app)
        self.trans_id_suffix = trans_id_suffix

    def handle_request(self,env,start_response):
        trans_id_suffix = self.trans_id_suffix
        trans_id_extra = env.get('HTTP_X_TRANS_ID_EXTRA')
        if trans_id_extra:
            trans_id_suffix += '-' + trans_id_extra[:32]
        trans_id = generate_trans_id(trans_id_suffix)
        env['swift.trans_id'] = trans_id

        try:
            resp = self.__app_call(env)
        except:
            resp = HTTPServerError # for next day

class CatchErrorMiddleware(object):
    """docstring for CatchErrorMiddleware"""
    def __init__(self, app, conf):
        pass  # (WIS) print "%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami())
        self.app = app
        self.conf = conf
        self.trans_id_suffix = conf.get('trans_id_suffix')

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        context = CatchErrorsContext(self.app, self.trans_id_suffix)

        #return self.__class__.__name__ + "  ->  " + self.app(env, start_response)
        return context


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        return CatchErrorMiddleware(app, conf)
    return except_filter
