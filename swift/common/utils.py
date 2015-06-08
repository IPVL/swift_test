import os
import sys
import uuid
import time

import codecs
utf8_decoder = codecs.getdecoder('utf-8')
utf8_encoder = codecs.getencoder('utf-8')

from optparse import OptionParser
from urllib import quote as _quote
from swift import gettext_ as _


def generate_trans_id(trans_id_suffix):
    return 'tx%s-%010x%s' %(
        uuid.uuid4().hex[:21],time.time(),quote(trans_id_suffix))


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

def get_valid_uft8_str(str_or_unicode):
    if isinstance(str_or_unicode,unicode):
        (str_or_unicode,_len) = utf8_encoder(str_or_unicode,'replace')
    (valid_utf8_str,_len)= utf8_decoder(str_or_unicode,'replace')
    return valid_utf8_str.encode('utf8-8')

def quote(value,safe='/'):
    return _quote(get_valid_uft8_str(value),safe)