"""
A two-part middleware which modifies request.COOKIES and adds a set and delete method.

    `set` matches django.http.HttpResponse.set_cookie
    `delete` matches django.http.HttpResponse.delete_cookie

MIDDLEWARE_CLASSES = (
    'djcookies.CookieMiddleware',
    ...
)

def my_view(request):
    request.COOKIES.set([args])
    ...
    return response
"""

from Cookie import SimpleCookie, Morsel
import copy


class CookieMiddleware(object):
    """
    This middleware modifies request.COOKIES and adds a set and delete method.
    It also updates the response with all modified cookies when finished

    `set` matches django.http.HttpResponse.set_cookie
    `delete` matches django.http.HttpResponse.delete_cookie

    This should be the first middleware you load.
    """
    def process_request(self, request):
        cookies = CookieHandler()
        for k, v in request.COOKIES.iteritems():
            cookies[k] = str(v)
        request.COOKIES = cookies
        request._orig_cookies = copy.deepcopy(request.COOKIES)

    def process_response(self, request, response):
        if hasattr(request, '_orig_cookies') and request.COOKIES != request._orig_cookies:
            for k, v in request.COOKIES.iteritems():
                if request._orig_cookies.get(k) != v:
                    dict.__setitem__(response.cookies, k, v)
        return response


class StringMorsel(Morsel):
    def __str__(self):
        return self.value or ''

    def __eq__(self, a):
        if isinstance(a, str):
            return str(self) == a
        elif isinstance(a, Morsel):
            return a.output() == self.output()
        return False

    def __ne__(self, a):
        if isinstance(a, str):
            return str(self) != a
        elif isinstance(a, Morsel):
            return a.output() != self.output()
        return True

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(str(self))

    def __nonzero__(self):
        return bool(str(self))

    def __contains__(self, obj):
        return obj in str(self)

    def __getattr__(self, name):
        try:
            return getattr(str(self), name)
        except AttributeError:
            msg = "%r object has no attribute '%s'"
            raise AttributeError(msg % (self.__class__.__name__, name))

    def __hash__(self):
        return hash(str(self))


class CookieHandler(SimpleCookie):
    def __set(self, key, real_value, coded_value):
        """Private method for setting a cookie's value"""
        M = self.get(key, StringMorsel())
        M.set(key, real_value, coded_value)
        dict.__setitem__(self, key, M)

    def __setitem__(self, key, value):
        """Dictionary style assignment."""
        rval, cval = self.value_encode(value)
        self.__set(key, rval, cval)

    def set(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=None):
        self[key] = value
        for var in ('max_age', 'path', 'domain', 'secure', 'expires'):
            val = locals()[var]
            if val is not None:
                self[key][var.replace('_', '-')] = val

    def delete(self, key, path='/', domain=None):
        self[key] = ''
        if path is not None:
            self[key]['path'] = path
        if domain is not None:
            self[key]['domain'] = domain
        self[key]['expires'] = 0
        self[key]['max-age'] = 0
