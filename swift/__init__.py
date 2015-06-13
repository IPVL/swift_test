#TODO: Demo

print 'Hello 1'

import os
import logging.config
# logging.config.fileConfig('../logging.conf', disable_existing_loggers=False)
# print 'File %s' % os.path.join(os.path.dirname(__file__))
# basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def gettext_(msg):
    # return _t.gettext(msg)
    return msg