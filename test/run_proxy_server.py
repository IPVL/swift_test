from os.path import isfile

import sys
from swift.common.utils import parse_options
from swift.common.wsgi import run_wsgi

pass  # (clac) print 'Number of arguments:', len(sys.argv), 'arguments.'
pass  # (clac) print 'Argument List:', str(sys.argv)

if __name__ == '__main__':
    conf_file, options = parse_options()
    conf = 'proxy-server.conf'
    if len(sys.argv) >= 2 and isfile(sys.argv[1]):
        conf = sys.argv[1]
    run_wsgi(conf, 'proxy-server')
