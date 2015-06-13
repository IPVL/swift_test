from __future__ import print_function
import os,itertools
import sys
import uuid
import time
import errno
import random
import weakref
import codecs
from logging.handlers import SysLogHandler
import logging

utf8_decoder = codecs.getdecoder('utf-8')
utf8_encoder = codecs.getencoder('utf-8')

from optparse import OptionParser
from urllib import quote as _quote
from swift import gettext_ as _
from eventlet.green import socket,threading
from eventlet import Timeout

class StatsdClient(object):
    def __init__(self,host,port,base_prefix = '',tail_prefix = '',default_sample_rate = 1,sample_rate_factor=1,logger = 1):
        self._host = host
        self._port = port
        self._base_prefix = base_prefix
        self.set_prefix(tail_prefix)
        self._default_sample_rate = default_sample_rate
        self._sample_rate_factor = sample_rate_factor
        self._target = (self._host,self._port)
        self.random = random
        self.logger = logger

    def set_prefix(self,new_prefix):
        if new_prefix and self._base_prefix:
            self._prefix = '.'.join([self._base_prefix,new_prefix,''])
        elif new_prefix:
            self._prefix = new_prefix + '.'
        elif self._base_prefix:
            self._prefix = self._base_prefix+'.'
        else:
            self._prefix= ''



class LoggingHandlerWeakRef(weakref.ref):
    """
    Like a weak reference, but passes through a couple methods that logging
    handlers need.
    """

    def close(self):
        referent = self()
        try:
            if referent:
                referent.close()
        except KeyError:
            pass

    def flush(self):
        referent = self()
        if referent:
            referent.flush()




class LogAdapter(logging.LoggerAdapter,object):
    _cls_thread_local = threading.local()

    def __init__(self,logger,server):
        logging.LoggerAdapter.__init__(self,logger,{})
        self.server = server
        setattr(self,'warn',self.warning)

    @property
    def txn_id(self):
        if hasattr(self._cls_thread_local,'txn_id'):
            return self._cls_thread_local.txn_id

    @txn_id.setter
    def txn_id(self,value):
        self._cls_thread_local = value

    @property
    def client_ip(self):
        if hasattr(self._cls_thread_local,'client_ip'):
            return self._cls_thread_local

    @client_ip.setter
    def client_ip(self,value):
        self._cls_thread_local = value

    @property
    def thread_locals(self):
        return (self.txn_id,self.client_ip)

    @thread_locals.setter
    def thread_locals(self,value):
        self.txn_id,self.client_ip = value

    def getEffectiveLevel(self):
        return self.logger.getEffectiveLevel()

    def process(self, msg, kwargs):

        kwargs['extra'] = {'server':self.server,'txn_id':self.txn_id,'client_ip':self.client_ip}
        return msg,kwargs


    def _exception(self,msg,*args,**kwargs):
        logging.LoggerAdapter.exception(self,msg,*args,**kwargs)


    def exception(self, msg, *args, **kwargs):

        _junk,exc,_junk = sys.exc_info()
        call = self.error
        emsg = ''

        if isinstance(exc,OSError):
            if exc.errno in (errno.EIO,errno.ENOSPC):
                emsg = str(exc)
            else:
                call = self._exception
        elif isinstance(exc, socket.error):
            if exc.errno == errno.ECONNREFUSED:
                emsg = _('Connection refused')
            elif exc.errno == errno.EHOSTUNREACH:
                emsg = _('Host unreachable')
            elif exc.errno == errno.ETIMEDOUT:
                emsg = _('Connection timeout')
            else:
                call = self._exception
        elif isinstance(exc, Timeout):
            emsg = exc.__class__.__name__
            if hasattr(exc,'seconds'):
                emsg += '(%ss)'%exc.seconds
            # if isinstance(exc, swift.common.exceptions.MessageTimeout):
            #     if exc.msg:
            #         emsg += ' %s' % exc.msg

        else:
            call = self._exception
        call('%s %s' %(msg,emsg),*args,**kwargs)

class SwiftLogFormatter(logging.Formatter):
    """
    Custom logging.Formatter will append txn_id to a log message if the
    record has one and the message does not. Optionally it can shorten
    overly long log lines.
    """

    def __init__(self,fmt = None,datefmt = None,max_line_length = 0):
        logging.Formatter.__init__(self, fmt=fmt, datefmt = datefmt)
        self.max_line_length = max_line_length

    def format(self, record):
        if not hasattr(record,'server'):
            record.server = record.name
        record.message = record.getMessage()

        if self._fmt.find('%(asctime)') >=0:
            record.asctime = self.formatTime(record,self.datefmt)
        msg = (self._fmt % record.__dict__).replace('\n','#012')
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info).replace('\n','#012')

        if record.exc_text:
            if msg[-3:]!='#012':
                msg = msg + '#012'
            msg = msg + record.exc_text
        if (hasattr(record,'txn_id') and record.txn_id and record.levelno != logging.INFO and record.txn_id not in msg):
            msg = '%s(txn: %s)'%(msg,record.txn_id)

        if (hasattr(record, 'client_ip') and record.client_ip and
                record.levelno != logging.INFO and
                record.client_ip not in msg):
            msg = "%s (client_ip: %s)" % (msg, record.client_ip)
        if self.max_line_length > 0 and len(msg) > self.max_line_length:
            if self.max_line_length < 7:
                msg = msg[:self.max_line_length]
            else:
                approxhalf = (self.max_line_length - 5) / 2
                msg = msg[:approxhalf] + " ... " + msg[-approxhalf:]
        return msg


def get_logger(conf,name=None,log_to_console=False,log_route=None,fmt="%(server)s: %(message)s"):
    """
    Get the current system logger using config settings.

    **Log config and defaults**::

        log_facility = LOG_LOCAL0
        log_level = INFO
        log_name = swift
        log_max_line_length = 0
        log_udp_host = (disabled)
        log_udp_port = logging.handlers.SYSLOG_UDP_PORT
        log_address = /dev/log
        log_statsd_host = (disabled)
        log_statsd_port = 8125
        log_statsd_default_sample_rate = 1.0
        log_statsd_sample_rate_factor = 1.0
        log_statsd_metric_prefix = (empty-string)

    :param conf: Configuration dict to read settings from
    :param name: Name of the logger
    :param log_to_console: Add handler which writes to console on stderr
    :param log_route: Route for the logging, not emitted to the log, just used
                      to separate logging configurations
    :param fmt: Override log format
    """
    if not conf:
        conf ={}
    if name is None:
        name = conf.get('log_name','swift')
    if not log_route:
        log_route = name
    logger = logging.getLogger(log_route)
    logger.propagate= False

    formatter = SwiftLogFormatter(fmt = fmt,max_line_length=int(conf.get('log_max_line_length',0)))

    if not hasattr(get_logger,'handler4logger'):
        get_logger.handler4logger = {}
    if logger in get_logger.handler4logger:
        logger.removeHandler(get_logger.handler4logger[logger])
    facility = getattr(SysLogHandler,conf.get('log_facility','LOG_LOCAL0'),SysLogHandler.LOG_LOCAL0)
    udp_host = conf.get('log_udp_host')

    if udp_host:
        udp_port = int(conf.get('log_udp_port',logging.handlers.SYSLOG_UDP_PORT))
        handler = SysLogHandler(address=(udp_host,udp_port),facility=facility)
    else:
        log_address = conf.get('log_address','/dev/log')
        try:
            handler = SysLogHandler(address=log_address,facility=facility)
        except socket.error as e:
            if e.errno not in [errno.ENOTSOCK, errno.ENOENT]:
                raise e
            handler = SysLogHandler(facility = facility)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    get_logger.handler4logger[logger] = handler

    if log_to_console or hasattr(get_logger,'console_handler4logger'):
        if not hasattr(get_logger,'console_handler4logger'):
            get_logger.console_handler4logger = {}

        if logger in get_logger.console_handler4logger:
            logger.removeHandler(get_logger.console_handler4logger[logger])

        console_handler = logging.StreamHandler(sys.__stderr__)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        get_logger.console_handler4logger[logger] = console_handler


    logger.setLevel(
        getattr(logging,conf.get('log_level','INFO').upper(),logging.INFO))

    statsd_host = conf.get('log_statsd_host')
    if statsd_host:
        statsd_port = int(conf.get('log_statsd_port',8125))
        base_prefix = conf.get('log_statsd_metric_prefix','')
        default_sample_rate = float(conf.get('log_statsd_default_sample_rate',1))
        sample_rate_factor = float(conf.get(
            'log_statsd_sample_rate_factor', 1))
        statsd_client = StatsdClient(statsd_host, statsd_port, base_prefix,
                                     name, default_sample_rate, sample_rate_factor, logger=logger)
        logger.statsd_client = statsd_host
    else:
        logger.statsd_client = None

    adapted_logger = LogAdapter(logger,name)
    other_handlers = conf.get('log_custom_handlers', None)
    if other_handlers:
        log_custom_handlers = [s.strip() for s in other_handlers.split(',') if s.strip()]
        for hook in log_custom_handlers:
            try:
                mod, fnc = hook.rsplit(',',1)
                logger_hook = getattr(__import__(mod,fromlist=[fnc]),fnc)
                logger_hook(conf,name,log_to_console,log_route,fmt,logger,adapted_logger)
            except (AttributeError,ImportError):
                print('Error calling custom handler [%s]'%hook,file= sys.stderr)
            except ValueError:
                print('Invalid custom handler format [%s]'%hook,file=sys.stderr)

    if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
        try:
            logging._acquireLock()
            for handler in adapted_logger.logger.handlers:
                if handler in logging._handlers:
                    wr = LoggingHandlerWeakRef(handler)
                    del logging._handlers[handler]
                    logging._handlers[wr] =1
                for i, handler_ref in enumerate(logging._handlerList):
                    if handler_ref is handler:
                        logging._handlerList[i] = LoggingHandlerWeakRef(handler)
        finally:
            logging._releaseLock()
    return adapted_logger




def generate_trans_id(trans_id_suffix):
    print('in generate_trans_id function')
    a = uuid.uuid4().hex[:21]
    print('a = %s' %a)
    b = time.time()
    print('b = %s '% b)
    c = quote(trans_id_suffix)
    print('and c = %s '%(c))

    # return 'tx%s-%010x%s' % (uuid.uuid4().hex[:21], time.time(), quote(trans_id_suffix))
    return 'tx%s-%010x%s' % (a,b, c)

def parse_options(parser=None, once=False, test_args=None):
    """
    Parse standard swift server/daemon options with optparse.OptionParser.

    :param parser: OptionParser to use. If not sent one will be created.
    :param once: Boolean indicating the "once" option is available
    :param test_args: Override sys.argv; used in testing

    :returns : Tuple of (config, options); config is an absolute path to the
               config file, options is the parser options as a dictionary.

    :raises SystemExit: First arg (CONFIG) is required, file must exist
    """
    if not parser:
        parser = OptionParser(usage="%prog CONFIG [options]")
    parser.add_option("-v", "--verbose", default=False, action="store_true",
                      help="log to console")
    if once:
        parser.add_option("-o", "--once", default=False, action="store_true",
                          help="only run one pass of daemon")

    # if test_args is None, optparse will use sys.argv[:1]
    options, args = parser.parse_args(args=test_args)

    if not args:
        parser.print_usage()
        print(_("Error: missing config path argument"))
        sys.exit(1)
    config = os.path.abspath(args.pop(0))
    if not os.path.exists(config):
        parser.print_usage()
        print(_("Error: unable to locate %s") % config)
        sys.exit(1)

    extra_args = []
    # if any named options appear in remaining args, set the option to True
    for arg in args:
        if arg in options.__dict__:
            setattr(options, arg, True)
        else:
            extra_args.append(arg)

    options = vars(options)
    if extra_args:
        options['extra_args'] = extra_args
    return config, options

def get_valid_utf8_str(str_or_unicode):
    print('get_valid_utf_str function ')
    if isinstance(str_or_unicode, unicode):
        (str_or_unicode, _len) = utf8_encoder(str_or_unicode,'replace')
        print('str_or_unicode = %s,_len = %s'%(str_or_unicode,_len))

    if str_or_unicode is None:
        print('None object cannot be unicoded')
        return None
        #raise TypeError('None object cannot be unicoded')
    (valid_utf8_str, _len)= utf8_decoder(str_or_unicode,'replace')
    print('valid_utf8_str = %s,_len = %s'%(valid_utf8_str,_len))
    return valid_utf8_str.encode('utf-8')

def quote(value, safe='/'):
    print('in quote function ')
    # return _quote(get_valid_utf8_str(value), safe)
    if value is None:
           return ''
    return _quote(get_valid_utf8_str(value), safe)

class CloseableChain(object):
    """
    Like itertools.chain, but with a close method that will attempt to invoke
    its sub-iterators' close methods, if any.
    """
    def __init__(self, *iterables):
        self.iterables = iterables

    def __iter__(self):
        return iter(itertools.chain(*(self.iterables)))

    def close(self):
        for it in self.iterables:
            close_method = getattr(it, 'close', None)
            if close_method:
                close_method()

