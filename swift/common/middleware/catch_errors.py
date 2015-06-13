from swift.ipvl.inspect_custom import whoami, whosdaddy
from swift.common.utils import generate_trans_id
from swift.common.wsgi import WSGIContext
from swift.common.swob import HTTPServerError
pass  # (WIS) print __name__
from swift import gettext_ as _
import logging
import logging.config

logging.config.fileConfig('logFile.conf')
logger = logging.getLogger('catch_error')

logger.debug('this is log test')
logger.info('this is logger in catch-errors')


class CatchErrorsContext(WSGIContext):
    def __init__(self,app,logger,trans_id_suffix=''):
        logger.info("++++++++++++++++++++++++start(__init__)++++in CatchErrorsContext class+++++++++++++++++++in catch_error.py")
        print('app = %s and logger = %s'%(app,logger))
        super(CatchErrorsContext,self).__init__(app)
        self.trans_id_suffix = trans_id_suffix
        self.logger = logger
        self.logger.info("++++++++++++++++++++++++end(__init__)+++++++++++++++++++++++in catch_error.py")

    def handle_request(self,env,start_response):
        self.logger.info("++++++++++++++++++++++++start(handle_request)+++++++++++++++++++++++in catch_error.py")
        self.logger.info('before adding tran_id environment = %s'% env)
        trans_id_suffix = self.trans_id_suffix
        print 'suffix = %s'%trans_id_suffix
        trans_id_extra = env.get('HTTP_X_TRANS_ID_EXTRA',None)
        if trans_id_extra:
            trans_id_suffix += '-' + trans_id_extra[:32]
        trans_id = generate_trans_id(trans_id_suffix)
        # trans_id = 'abc123sujon'
        logger.debug('trans_id')
        self.logger.debug('transiction id ..')
        print('trans_id = %s '% trans_id)
        env['swift.trans_id'] = trans_id

        try:
            print('this is app call')
            self.logger.info('after adding tran_id environment = %s'% env)
            resp = self._app_call(env)
            print('resp in handle request in catch_error.py in try block= %s'%resp)
        except:
            logger.debug('Error: An error occurred')
            self.logger.exception(_('Error: An error occurred'))
            resp = HTTPServerError() # for next day
            resp.headers['X-Trans-Id'] = trans_id
            return resp(env,start_response)

        if self._response_headers is None:
            self._response_headers = []
        self._response_headers.append(('X-Trans_Id',trans_id))
        start_response(self._response_status,self._response_headers,self._response_exc_info)
        self.logger.info('response_header = %s'% self._response_headers)
        self.logger.info('start_response = %s'% start_response)
        self.logger.info("++++++++++++++++++++++++end (handle_request)+++++++++++++++++++++++in catch_error.py")
        return resp

class CatchErrorMiddleware(object):
    """docstring for CatchErrorMiddleware"""
    def __init__(self, app, conf):
        pass  # (WIS)
        logger.info("%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami()))
        self.app = app
        # self.logger = get_logger(conf,log_route='catch-errors')
        self.logger = logging.getLogger('catch-errors')
        self.trans_id_suffix = conf.get('trans_id_suffix')

    def __call__(self, env, start_response):
        pass  # (WIS) print "%s %s\n" % (self.__class__.__name__, env)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        context = CatchErrorsContext(self.app,
                                     self.logger,
                                     self.trans_id_suffix)

        # return self.__class__.__name__ + "  ->  " + self.app(env, start_response)
        print 'env = ',env,
        print 'start response = %s'%start_response
        return context.handle_request(env,start_response)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
        print('app = %s'%app)
        logger.info("%s (%s -> %s)" % (__name__, whosdaddy(), whoami()))
        return CatchErrorMiddleware(app, conf)
    return except_filter
