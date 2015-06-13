# from swift.ipvl.inspect_custom import whoami, whosdaddy
#
# import re
# from swift.common.request_helpers import get_sys_meta_prefix,remove_items
# from swift.common.swob import Request
#
#
# import logging
# import logging.config
# logging.config.fileConfig('logFile1.conf')
# logger = logging.getLogger('gatekeeper')
#
# pass  # (WIS) print __name__
#
#
# inbound_exclusions = [get_sys_meta_prefix('account'),
#                       get_sys_meta_prefix('container'),
#                       get_sys_meta_prefix('object'),
#                       'x-backend']
#
#
# outbound_exclusions = inbound_exclusions
#
#
#
# def make_exclusion_test(exclusions):
#     logger.info('++++++++++++++++++++++start(make_exclusion_test) ++++++++++in gatekeeper.py')
#     expr = '|'.join(exclusions)
#     test = re.compile(expr,re.IGNORECASE)
#     logger.info('exclusions = %s , expr = %s and test = %s'%(exclusions,expr,test))
#     logger.info('++++++++++++++++++++++end(make_exclusion_test) ++++++++++in getkepper.py')
#     return test.match
#
#
#
# class GatekeeperMiddleware(object):
#     """docstring for GatekeeperMiddleware"""
#
#
#     def __init__(self, app, conf):
#         logger.info('++++++++++++++++++++++start(__init__) ++++++++++in gatekeeper.py')
#         pass  # (WIS)
#         logger.info( "\n\n\n%s %s (%s -> %s)" % (__name__, self.__class__.__name__, whosdaddy(), whoami()))
#         logger.info('\n\n\n app = %s and conf = %s '%(app,conf))
#         self.app = app
#         self.conf = conf
#         self.logger = logging.getLogger('gatekeeper')
#         self.inbound_condition = make_exclusion_test(inbound_exclusions)
#         self.outbound_condition = make_exclusion_test(outbound_exclusions)
#         self.logger.info('inbound_condition = %s and outbound_condition = %s'%(self.inbound_condition,self.outbound_condition))
#         self.logger.info('++++++++++++++++++++++end(__init__) ++++++++++in gatekeeper.py')
#
#
#
#     def __call__(self, env, start_response):
#         pass  # (WIS)
#         self.logger.info('++++++++++++++++++++++start(__call__) ++++++++++in gatekeeper.py')
#         self.logger.info('env = %s and start_response = %s'%(env,start_response))
#         self.logger.info( "%s %s\n" % (self.__class__.__name__, env))
#
#         start_response('200 OK', [('Content-Type', 'text/plain')])
#         req = Request(env)
#         self.logger.info('request headers = %s ' %req.headers)
#         removed = remove_items(req.headers,self.inbound_condition)
#         if removed:
#             self.logger.debug('removed request headers: %s' % removed)
#
#         def gatekeeper_response(status,response_headers,exc_info = None):
#
#             removed = filter(
#                 lambda h:self.outbound_condition(h[0]),response_headers)
#             if removed:
#                 self.logger.debug('removed response headers: %s' % removed)
#                 new_headers = filter(lambda h:not self.outbound_condition(h[0]),response_headers)
#                 return start_response(status,new_headers,exc_info)
#             return start_response(status,response_headers,exc_info)
#
#         return self.__class__.__name__ + "  ->  " + self.app(env, start_response)
#         # self.logger.info(self.__class__.__name__ + "  ->  " + self.app(env, start_response))
#         # return self.app(env,gatekeeper_response)
#
#
#
#
# def filter_factory(global_conf, **local_conf):
#     """Returns a WSGI filter app for use with paste.deploy."""
#     logger.info('++++++++++++++++++++++start(filter_factory) ++++++++++in gatekeeper.py')
#     pass  # (WIS)
#     logger.info("%s (%s -> %s)" % (__name__, whosdaddy(), whoami()))
#     conf = global_conf.copy()
#     conf.update(local_conf)
#     logger.info('conf  = %s'%(conf))
#
#     def gatekeeper_filter(app):
#         pass  # (WIS) print "%s (%s -> %s)" % (__name__, whosdaddy(), whoami())
#         logger.info('++++++++++++++++++++++start(gatekeeper_filter) and return GatekeeperMiddleware ++++++++++in gatekeeper.py')
#         return GatekeeperMiddleware(app, conf)
#     logger.info('++++++++++++++++++++++end(filter_factory) ++++++++++in gatekeeper.py')
#     return gatekeeper_filter


from swift.common.swob import Request
from swift.common.utils import get_logger
from swift.common.request_helpers import remove_items, get_sys_meta_prefix
import re

import logging
# import logging.config
# logging.config.fileConfig('logFile1.conf', disable_existing_loggers=False)
logger = logging.getLogger('gateKepper')

logger.debug('this is log test in gatekepper')

#: A list of python regular expressions that will be used to
#: match against inbound request headers. Matching headers will
#: be removed from the request.
# Exclude headers starting with a sysmeta prefix.
# If adding to this list, note that these are regex patterns,
# so use a trailing $ to constrain to an exact header match
# rather than prefix match.
inbound_exclusions = [get_sys_meta_prefix('account'),
                      get_sys_meta_prefix('container'),
                      get_sys_meta_prefix('object'),
                      'x-backend']
# 'x-object-sysmeta' is reserved in anticipation of future support
# for system metadata being applied to objects


#: A list of python regular expressions that will be used to
#: match against outbound response headers. Matching headers will
#: be removed from the response.
outbound_exclusions = inbound_exclusions


def make_exclusion_test(exclusions):
    logger.info('++++++++++++++++++++++start(make_exclusion_test) ++++++++++in gatekeeper.py')
    expr = '|'.join(exclusions)
    test = re.compile(expr, re.IGNORECASE)
    logger.info('exclusions = %s , expr = %s and test = %s'%(exclusions,expr,test))
    logger.info('++++++++++++++++++++++end(make_exclusion_test) ++++++++++in getkepper.py')
    return test.match


class GatekeeperMiddleware(object):
    def __init__(self, app, conf):
        logger.debug('++++++++++++++++++++++start(__init__) ++++++++++in gatekeeper.py')
        logger.debug('app = %s and conf = %s '%(app,conf))
        self.app = app
        self.logger = logging.getLogger('gatekeeper')
        self.inbound_condition = make_exclusion_test(inbound_exclusions)
        self.outbound_condition = make_exclusion_test(outbound_exclusions)
        logger.debug('logger = %s, inbound_condition = %s and outbound_condition = %s'%(self.logger,self.inbound_condition,self.outbound_condition))
        logger.debug('++++++++++++++++++++++end(__init__) ++++++++++in gatekeeper.py')
    def __call__(self, env, start_response):
        logger.debug('++++++++++++++++++++++start(__call__) ++++++++++in gatekeeper.py')
        logger.debug('env = %s and start_response = %s'%(env,start_response))
        req = Request(env)
        logger.debug('req = %s '%req)
        logger.info('requested header = %s'%req.headers)
        removed = remove_items(req.headers, self.inbound_condition)
        logger.info('removed  = %s and inbound_condition = %s '%(removed,self.inbound_condition))
        if removed:
            self.logger.debug('removed request headers: %s' % removed)
        logger.info('++++++++++++++++++++++end(__call__) ++++++++++in gatekeeper.py')
        def gatekeeper_response(status, response_headers, exc_info=None):
            logger.info('++++++++++++++++++++++start(gatekeeper_response) ++++++++++in gatekeeper.py')

            removed = filter(
                lambda h: self.outbound_condition(h[0]),
                response_headers)
            if removed:
                self.logger.debug('removed response headers: %s' % removed)
                new_headers = filter(
                    lambda h: not self.outbound_condition(h[0]),
                    response_headers)
                return start_response(status, new_headers, exc_info)
            logger.info('++++++++++++++++++++++end(gatekeeper_response) ++++++++++in gatekeeper.py')
            return start_response(status, response_headers, exc_info)
        logger.info('++++++++++++++++++++++end(__call__) ++++++++++in gatekeeper.py')
        logger.info('self.app = %s ' %self.app)
        return self.app(env, gatekeeper_response)


def filter_factory(global_conf, **local_conf):
    logger.info('++++++++++++++++++++++start(filter_factory) ++++++++++in gatekeeper.py')

    conf = global_conf.copy()
    conf.update(local_conf)
    logger.info('global_conf %s and local_conf = %s'%(global_conf,local_conf))
    logger.info('conf = %s'%conf)
    def gatekeeper_filter(app):
        logger.info('++++++++++++++++++++++start (gatekeeper_filter) and return GatekeeperMiddleware ++++++++++in gatekeeper.py')
        return GatekeeperMiddleware(app, conf)
    logger.info('++++++++++++++++++++++end(filter_factory) ++++++++++in gatekeeper.py')
    return gatekeeper_filter
