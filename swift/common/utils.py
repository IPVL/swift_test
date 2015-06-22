import os
import sys
from optparse import OptionParser

from swift import gettext_ as _


def get_hub():
    """
    Checks whether poll is available and falls back
    on select if it isn't.

    Note about epoll:

    Review: https://review.openstack.org/#/c/18806/

    There was a problem where once out of every 30 quadrillion
    connections, a coroutine wouldn't wake up when the client
    closed its end. Epoll was not reporting the event or it was
    getting swallowed somewhere. Then when that file descriptor
    was re-used, eventlet would freak right out because it still
    thought it was waiting for activity from it in some other coro.
    """
    try:
        import select
        if hasattr(select, "poll"):
            return "poll"
        return "selects"
    except ImportError:
        return None


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
