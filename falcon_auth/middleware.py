# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

import falcon

from falcon_auth.backends import AuthBackend, AuthBackend_async

class FalconAuthMiddleware(object):

    """
    Creates a falcon auth middleware that uses given authentication backend, and some
    optional configuration to authenticate requests. After initializing the
    authentication backend globally you can override the backend as well as
    other configuration for a particular resource by setting the `auth` attribute
    on it to an instance of this class.

    The authentication backend must return an authenticated user which is then
    set as `request.context.user` to be used further down by resources otherwise
    an `falcon.HTTPUnauthorized` exception is raised.

    Args:
        backend(:class:`falcon_auth.backends.AuthBackend`, required): Specifies the auth
            backend to be used to authenticate requests

        exempt_routes(list, optional): A list of paths to be excluded while performing
            authentication. Default is ``None``

        exempt_methods(list, optional): A list of paths to be excluded while performing
            authentication. Default is ``['OPTIONS']``

    """

    def __init__(self, backend, exempt_routes=None, exempt_methods=None):
        self.backend = backend
        if not isinstance(backend, AuthBackend):
            raise ValueError(
                'Invalid authentication backend {0}. '
                'Must inherit `falcon.auth.backends.AuthBackend`'.format(backend)
            )

        self.exempt_routes = exempt_routes or []
        self.exempt_methods = exempt_methods or ['OPTIONS']

    def _get_auth_settings(self, req, resource):
        auth_settings = getattr(resource, 'auth', {})
        auth_settings['exempt_routes'] = self.exempt_routes
        if auth_settings.get('auth_disabled'):
            auth_settings['exempt_routes'].append(req.uri_template)

        for key in ('exempt_methods', 'backend'):
            auth_settings[key] = auth_settings.get(key) or getattr(self, key)

        return auth_settings

    def process_resource(self, req, resp, resource, *args, **kwargs):
        auth_setting = self._get_auth_settings(req, resource)
        if (req.uri_template in auth_setting['exempt_routes'] or
            req.method in auth_setting['exempt_methods']):
            return

        backend = auth_setting['backend']
        req.context['user'] = backend.authenticate(req, resp, resource, **kwargs)


class FalconAuthMiddleware_async(object):

    """
    Creates a falcon auth middleware that uses given authentication backend, and some
    optional configuration to authenticate requests. After initializing the
    authentication backend globally you can override the backend as well as
    other configuration for a particular resource by setting the `auth` attribute
    on it to an instance of this class.
    The authentication backend must return an authenticated user which is then
    set as `request.context.user` to be used further down by resources otherwise
    an `falcon.HTTPUnauthorized` exception is raised.
    Args:
        backend(:class:`falcon_auth.backends.AuthBackend`, required): Specifies the auth
            backend to be used to authenticate requests
        exempt_routes(list, optional): A list of paths to be excluded while performing
            authentication. Default is ``None``
        exempt_methods(list, optional): A list of paths to be excluded while performing
            authentication. Default is ``['OPTIONS']``
    """

    def __init__(self, backend, exempt_routes=None, exempt_methods=None):
        self.backend = backend
        if not isinstance(backend, AuthBackend) and not isinstance(backend, AuthBackend_async):
            raise ValueError(
                'Invalid authentication backend {0}. '
                'Must inherit `falcon.auth.backends.AuthBackend` or `falcon.auth.backends.AuthBackend_async`'.format(backend)
            )

        self.exempt_routes = exempt_routes or []
        self.exempt_methods = exempt_methods or ['OPTIONS']

    async def _get_auth_settings(self, req, resource):
        auth_settings = getattr(resource, 'auth', {})
        auth_settings['exempt_routes'] = self.exempt_routes
        if auth_settings.get('auth_disabled'):
            auth_settings['exempt_routes'].append(req.uri_template)

        for key in ('exempt_methods', 'backend'):
            auth_settings[key] = auth_settings.get(key) or getattr(self, key)

        return auth_settings

    async def process_resource(self, req, resp, resource, *args, **kwargs):
        auth_setting = await self._get_auth_settings(req, resource)
        if (req.uri_template in auth_setting['exempt_routes'] or
            req.method in auth_setting['exempt_methods']):
            return

        backend = auth_setting['backend']
        if backend.__class__.__name__.endswith("_async"):
            req.context['user'] = await backend.authenticate(req, resp, resource, **kwargs)
        else:
            req.context['user'] = backend.authenticate(req, resp, resource, **kwargs)

    async def process_resource_ws(self, req, resp, resource, *args, **kwargs):
        auth_setting = await self._get_auth_settings(req, resource)
        if (req.uri_template in auth_setting['exempt_routes'] or
            req.method in auth_setting['exempt_methods']):
            return

        backend = auth_setting['backend']
        try:
            req.context['user'] = await backend.authenticate(req, resp, resource, **kwargs)
        except falcon.HTTPUnauthorized as e:
            # We need to let the WebSocket resource handle this, or the response code will be 1000
            pass

