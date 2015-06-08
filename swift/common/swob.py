from functools import partial
import UserDict
from email.utils import parsedate
from datetime import datetime,tzinfo,timedelta
import time




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
            host = ''

class Response(object):
    content_length = _header_int_property('content-length')
    content_type = _resp_content_type_property()
    content_range = _header_property('content-range')
    etag = _resp_etag_property()
    status = _resp_status_property()
    body = _resp_body_property()
    host_url = _host_url_property()
    last_modified = _datetime_property('last-modified')

    # def __init__(self,environ):
    #     self.environ = environ
    #     self.headers = HeaderEnvironProxy(self.environ)

class HTTPException(Response,Exception):
    def __init__(self,*args, **kwargs):
        Response.__init__(self,*args,**kwargs)
        Exception.__init__(self,self.status)
class StatusMap(object):
    def __getitem__(self, key):
        return partial(HTTPException,status = key)

status_map = StatusMap()


HTTPServerError = status_map[500]