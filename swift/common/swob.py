from functools import partial
import UserDict
from StringIO import StringIO

from email.utils import parsedate
from datetime import datetime,tzinfo,timedelta
import time
import random
import re


RESPONSE_REASONS = {
    100: ('Continue', ''),
    200: ('OK', ''),
    201: ('Created', ''),
    202: ('Accepted', 'The request is accepted for processing.'),
    204: ('No Content', ''),
    206: ('Partial Content', ''),
    301: ('Moved Permanently', 'The resource has moved permanently.'),
    302: ('Found', 'The resource has moved temporarily.'),
    303: ('See Other', 'The response to the request can be found under a '
          'different URI.'),
    304: ('Not Modified', ''),
    307: ('Temporary Redirect', 'The resource has moved temporarily.'),
    400: ('Bad Request', 'The server could not comply with the request since '
          'it is either malformed or otherwise incorrect.'),
    401: ('Unauthorized', 'This server could not verify that you are '
          'authorized to access the document you requested.'),
    402: ('Payment Required', 'Access was denied for financial reasons.'),
    403: ('Forbidden', 'Access was denied to this resource.'),
    404: ('Not Found', 'The resource could not be found.'),
    405: ('Method Not Allowed', 'The method is not allowed for this '
          'resource.'),
    406: ('Not Acceptable', 'The resource is not available in a format '
          'acceptable to your browser.'),
    408: ('Request Timeout', 'The server has waited too long for the request '
          'to be sent by the client.'),
    409: ('Conflict', 'There was a conflict when trying to complete '
          'your request.'),
    410: ('Gone', 'This resource is no longer available.'),
    411: ('Length Required', 'Content-Length header required.'),
    412: ('Precondition Failed', 'A precondition for this request was not '
          'met.'),
    413: ('Request Entity Too Large', 'The body of your request was too '
          'large for this server.'),
    414: ('Request URI Too Long', 'The request URI was too long for this '
          'server.'),
    415: ('Unsupported Media Type', 'The request media type is not '
          'supported by this server.'),
    416: ('Requested Range Not Satisfiable', 'The Range requested is not '
          'available.'),
    417: ('Expectation Failed', 'Expectation failed.'),
    422: ('Unprocessable Entity', 'Unable to process the contained '
          'instructions'),
    499: ('Client Disconnect', 'The client was disconnected during request.'),
    500: ('Internal Error', 'The server has either erred or is incapable of '
          'performing the requested operation.'),
    501: ('Not Implemented', 'The requested method is not implemented by '
          'this server.'),
    502: ('Bad Gateway', 'Bad gateway.'),
    503: ('Service Unavailable', 'The server is currently unavailable. '
          'Please try again at a later time.'),
    504: ('Gateway Timeout', 'A timeout has occurred speaking to a '
          'backend server.'),
    507: ('Insufficient Storage', 'There was not enough space to save the '
          'resource. Drive: %(drive)s'),
}

class _UTC(tzinfo):
    """
    A tzinfo class for datetime objects that returns a 0 timedelta (UTC time)
    """
    def dst(self,dt):
        return timedelta(0)
    utcoffset = dst

    def tzname(self, dt):
        return 'UTC'


UTC = _UTC()


class WsgiStringIO(StringIO):
    def set_hundred_continue_response_headers(self,headers):
        pass

    def send_hundred_continue_response(self):
        pass



def _datetime_property(header):
    def getter(self):
        value = self.headers.get(header,None)
        if value is not None:
            try:
                parts = parsedate(self.headers[header])[:7]
                return datetime(*(parts +(UTC,)))
            except Exception:
                return None

    def setter(self,value):
        if isinstance(value,(float,int,long)):
            self.headers[header] = time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        elif isinstance(value,datetime):
            self.headers[header] = value.strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            self.headers[header] = value

    return property(getter,setter,doc = ("Retrieve and set the %s header as a datetime, "
                         "set it with a datetime, int, or str") % header)


def _header_property(header):

    def getter(self):
        return self.headers.get(header,None)

    def setter(self,value):
        self.headers[header] = value


    return property(getter,setter,doc = 'Retrieve and set the %s header'%header)


def _header_int_property(header):
    def getter(self):
        val = self.headers.get(header,None)
        if val is not None:
            val = int(val)
        return val
    def setter(self,value):
        self.headers[header] = value

    return property(getter,setter,doc='Retrieve and set the %s header as an int' %header)

class HeaderEnvironProxy(UserDict.DictMixin):
    def __init__(self,environ):
        self.environ = environ

    def _normalize(self, key):
        key = 'HTTP_' + key.replace('-', '_').upper()
        if key == 'HTTP_CONTENT_LENGTH':
            return 'CONTENT_LENGTH'
        if key == 'HTTP_CONTENT_TYPE':
            return 'CONTENT_TYPE'
        return key

    def __getitem__(self, key):
        return self.environ[self._normalize(key)]

    def __setitem__(self, key, value):
        if value is None:
            self.environ.pop(self._normalize(key), None)
        elif isinstance(value, unicode):
            self.environ[self._normalize(key)] = value.encode('utf-8')
        else:
            self.environ[self._normalize(key)] = str(value)

    def __contains__(self, key):
        return self._normalize(key) in self.environ

    def __delitem__(self, key):
        del self.environ[self._normalize(key)]

    def keys(self):
        keys = [key[5:].replace('_', '-').title()
                for key in self.environ if key.startswith('HTTP_')]
        if 'CONTENT_LENGTH' in self.environ:
            keys.append('Content-Length')
        if 'CONTENT_TYPE' in self.environ:
            keys.append('Content-Type')
        return keys



def _resp_body_property():
    def getter(self):
        if not self._body:
            if not self._app_iter:
                return ''
            self._body = ''.join(self._app_iter)
            self._app_iter = None
        return self._body
    def setter(self,value):
        if isinstance(value,unicode):
            value = value.encode('utf-8')
        if isinstance(value,str):
            self.content_length = len(value)
            self._app_iter = None
        self._body = value

    return property(getter,setter,doc = 'Retrive and set the Response body str')

def _resp_etag_property():
    def getter(self):
        etag = self.headers.get('etag',None)
        if etag:
            etag = etag.replace("",'')
        return etag
    def setter(self,value):
        if value is None:
            self.headers['etag'] = None
        else:
            self.headers[''] = '"%s"'%value

    return property(getter,setter,doc='Retrieve and the response Etag header')


def _resp_content_type_property():
    def getter(self):
        if 'content-type' in self.headers:
            return self.headers.get('content-type').split(';')[0]
    def setter(self,value):
        self.headers['content-type'] = value

    return property(getter,setter,doc = 'Retrieve and set the Response Content-type header')

def _resp_charset_property():

    def getter(self):
        if '; charset' in self.headers['content-type']:
            return self.headers['content-type'].split(';charset=')[1]

    def setter(self,value):
        if 'content-type' in self.headers:
            self.headers['content-type'] = self.headers['content-type'].split(';')[0]
            if value:
                self.headers['content-type'] += '; charset='+value

    return property(getter,setter,doc='Retrieve and set the response charset')


def _resp_app_iter_property():
    """
    Set and retrieve Response.app_iter
    Mostly a pass-through to Response._app_iter; it's a property so it can zero
    out an existing content-length on assignment.
    """

    def getter(self):
        return self._app_iter

    def setter(self,value):
        if isinstance(value,(list,tuple)):
            self.content_length = sum(map(len,value))
        elif value is not None:
            self.content_length = None
            self._body = None
        self._app_iter = value

    return property(getter,setter,doc='Retrieve and set the response app_iter')


def _resp_status_property():
    def getter(self):
        return '%s %s'%(self.status_int,self.title)
    def setter(self,value):
        if isinstance(value,(int,long)):
            self.status_int = value
            self.explanation = self.title = RESPONSE_REASONS[value][0]


def _host_url_property():
    def getter(self):
        if 'HTTP_HOST' in self.environ:
            host = self.environ['HTTP_HOST']
        else:
            host = '%s:%s'%(self.environ['SERVER_NAME'],
                            self.environ['SERVER_PORT'])
        scheme = self.environ.get('wsgi.url_scheme', 'http')

        if scheme == 'http' and host.endswith(':80'):
            host, port = host.rsplit(':',1)
        elif scheme == 'https' and host.endswith(':443'):
            host,port = host.rsplit(':',1)
        return '%s://%s'%(scheme,host)

    return property(getter,doc='Get url for request/response up to path')

def _req_fancy_property(cls,header,even_if_nonexistent=False):

    def getter(self):
        try:
            if header in self.headers or even_if_nonexistent:
                return cls(self.headers.get(header))
        except ValueError:
            return None

    def setter(self,value):
        self.headers[header] = value

    return property(getter,setter,doc=("Retrieve and set the %s "
                    "property in the WSGI environ, as a %s object") %
                    (header, cls.__name__))

class Range(object):
    def __init__(self,headerval):
        headerval = headerval.replace(' ','')
        if not headerval.lower().startswith('bytes='):
            raise ValueError('Invalid Range header : %s'%headerval)
        self.ranges = []

        for rng in headerval[6:].split(','):
            if rng.find('-') == -1:
                raise ValueError('Invalid Range header: %s' % headerval)
            start,end = rng.split('-',1)

            if start:
                start = int(start)
            else:
                start = None

            if end:
                end = int(end)
                if start is not None and end <start:
                    raise ValueError('Invalid Range header: %s' % headerval)


            else:
                end = None
                if start is None:
                    raise ValueError('Invalid Range header: %s' % headerval)
            self.ranges.append(start,end)

    def __str__(self):
        string = 'bytes='
        for start, end in self.ranges:
            if start is not None:
                string += str(start)
            string += '-'
            if end is not None:
                 string += str(end)
            string += ','
        return string.rstrip(',')

class Match(object):

    def __init__(self,headerval):
        self.tags = set()
        for tag in headerval.split(', '):
            if tag.startswith('"') and tag.endswith('"'):
                self.tags.add(tag[1:-1])
            else:
                self.tags.add(tag)

    def __contains__(self, val):
        return '*' in self.tags or val in self.tags

class Accept(object):

    token = r'[^()<>@,;:\"/\[\]?={}\x00-\x20\x7f]+'
    qdtext = r'[^"]'
    quoted_pair = r'(?:\\.)'
    quoted_string = r'"(?:' + qdtext + r'|' + quoted_pair + r')*"'
    extension = (r'(?:\s*;\s*(?:' + token + r")\s*=\s*" + r'(?:' + token +
                 r'|' + quoted_string + r'))')
    acc = (r'^\s*(' + token + r')/(' + token +
           r')(' + extension + r'*?\s*)$')
    acc_pattern = re.compile(acc)

    def __init__(self,headerval):
        self.headerval = headerval

    def __repr__(self):
        return self.headerval


def _req_environ_property(environ_field):

    def getter(self):
        return self.environ.get(environ_field,None)

    def setter(self,value):
        if isinstance(value,unicode):
            self.environ[environ_field] = value.encode('utf-8')
        else:
            self.environ[environ_field] = value

    return property(getter,setter, doc=("Get and set the %s property "
                    "in the WSGI environment") % environ_field)

def _req_body_property():


    def getter(self):
        body = self.environ['wsgi.input'].read()
        self.environ['wsgi.input'] = WsgiStringIO(body)
        return body

    def setter(self,value):
        self.environ['wsgi.input'] = WsgiStringIO(value)
        self.environ['CONTENT_LENGTH'] = str(len(value))

    return property(getter,setter,doc='Get and set the request body str')


class Request(object):

    range = _req_fancy_property(Range,'range')
    if_none_match = _req_fancy_property(Match,'if_none_match')
    accept = _req_fancy_property(Accept,'accept',True)
    method = _req_environ_property('REQUEST_METHOD')
    referrer = referer = _req_environ_property('HTTP_REFERER')
    script_name = _req_environ_property('SCRIPT_NAME')
    path_info = _req_environ_property('PATH_INFO')
    host = _req_environ_property('HTTP_HOST')
    host_url = _host_url_property()
    remote_addr = _req_environ_property('REMOTE_ADDR')
    remote_user = _req_environ_property('REMOTE_USER')
    user_agent = _req_environ_property('HTTP_USER_AGENT')
    query_string = _req_environ_property('QUERY_STRING')
    if_match = _req_fancy_property(Match, 'if-match')
    body_file = _req_environ_property('wsgi.input')
    content_length= _header_int_property('content-length')
    if_modified_since = _datetime_property('if-modified-since')
    if_unmodified_since = _datetime_property('if-unmodified-since')
    body = _req_body_property()
    charset = None
    _params_cache = None
    _timestamp = None
    acl = _req_environ_property('swob.ACL')


    def __init__(self,environ):
        self.environ = environ
        self.headers = HeaderEnvironProxy(self.environ)



class Response(object):
    content_length = _header_int_property('content-length')
    content_type = _resp_content_type_property()
    content_range = _header_property('content-range')
    etag = _resp_etag_property()
    status = _resp_status_property()
    body = _resp_body_property()
    host_url = _host_url_property()
    last_modified = _datetime_property('last-modified')
    location = _header_property('location')
    accept_ranges = _header_property('accept-ranges')
    charset = _resp_charset_property()
    app_iter = _resp_app_iter_property()


    def __init__(self,body=None,status=200, headers = None,app_iter = None,request = None,conditional_response=False,
                 conditional_etag=None,**kw):
        self.headers = headers
        self.conditional_response = conditional_response
        self._conditional_etag = conditional_etag
        self.request = request
        self.body = body
        self.app_iter = app_iter
        self.status = status
        self.boundary = '%.32x'%random.randint(0,256 ** 16)
        if request:
            self.environ = request.environ
        else:
            self.environ = {}

        if headers:
            if self._body and 'Content-Length' in headers:
                # If body is not empty, prioritize actual body length over
                # content_length in headers
                del headers['Content-Length']
            self.headers.update(headers)
        if self.status_int == 401 and 'www-authenticate' not in self.headers:
            self.headers.update({'www-authenticate': self.www_authenticate()})
        for key, value in kw.iteritems():
            setattr(self, key, value)
        # When specifying both 'content_type' and 'charset' in the kwargs,
        # charset needs to be applied *after* content_type, otherwise charset
        # can get wiped out when content_type sorts later in dict order.
        if 'charset' in kw and 'content_type' in kw:
            self.charset = kw['charset']



class HTTPException(Response,Exception):
    def __init__(self,*args, **kwargs):
        Response.__init__(self,*args,**kwargs)
        Exception.__init__(self,self.status)
class StatusMap(object):
    def __getitem__(self, key):
        return partial(HTTPException,status = key)

status_map = StatusMap()

HTTPOk = status_map[200]
HTTPCreated = status_map[201]
HTTPAccepted = status_map[202]
HTTPUnauthorized = status_map[401]
HTTPServerError = status_map[500]