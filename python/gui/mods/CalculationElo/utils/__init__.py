# -*- coding: utf-8 -*-
import json
import logging
import os
import weakref
import BigWorld
from wg_async import wg_async, AsyncReturn, await_callback

from .elo_changes import calculate_elo_changes


def byteify(data):
    try:
        _unicode = unicode
    except NameError:
        _unicode = str

    if isinstance(data, dict):
        try:
            items = data.iteritems()
        except AttributeError:
            items = data.items()
        return {byteify(key): byteify(value) for key, value in items}
    elif isinstance(data, (list, tuple)):
        return [byteify(element) for element in data]
    elif isinstance(data, set):
        return [byteify(element) for element in data]
    elif isinstance(data, _unicode):
        return data.encode('utf-8')
    return data


def override(holder, name, wrapper=None, setter=None):
    import types

    if wrapper is None:
        return lambda wrapper, setter=None: override(holder, name, wrapper, setter)

    target = getattr(holder, name)

    wrapped = lambda *a, **kw: wrapper(target, *a, **kw)

    if not isinstance(holder, types.ModuleType) and isinstance(target, types.FunctionType):
        setattr(holder, name, staticmethod(wrapped))
    elif isinstance(target, property):
        prop_getter = lambda *a, **kw: wrapper(target.fget, *a, **kw)
        prop_setter = (lambda *a, **kw: setter(target.fset, *a, **kw)) if setter else target.fset
        setattr(holder, name, property(prop_getter, prop_setter, target.fdel))
    else:
        setattr(holder, name, wrapped)

__all__ = [
    'logger',
    'fetch_data_with_retry',
    'calculate_elo_changes',
    'weak_callback',
    'get_battle_level',
    'cancelCallbackSafe',
    'ApiFallbackRequester',
    'byteify',
    'override'
]

logger = logging.getLogger('CalculationElo')

if not logger.handlers:
    _is_debug = os.path.isfile('.debug_mods')

    if _is_debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter('[%(name)s] %(levelname)s: %(message)s'))
    _handler.setLevel(logging.DEBUG if _is_debug else logging.INFO)

    logger.addHandler(_handler)
    logger.propagate = False


def cancelCallbackSafe(cbid):
    try:
        if cbid is not None:
            BigWorld.cancelCallback(cbid)
            return True
    except (AttributeError, ValueError):
        pass
    return False


def weak_callback(obj, method_name, *args):
    ref = weakref.ref(obj)
    def _cb():
        instance = ref()
        if instance is not None:
            getattr(instance, method_name)(*args)
    return _cb


def get_battle_level(tankTier):
    if tankTier <= 6:
        return 6
    elif tankTier <= 8:
        return 8
    return 10


def _internal_fetch(url, headers, timeout, method, postData, callback):
    return BigWorld.fetchURL(
        url,
        callback,
        headers,
        timeout,
        method,
        postData
    )


@wg_async
def _async_sleep(seconds):
    yield await_callback(lambda cb: BigWorld.callback(seconds, lambda: cb(None)))()


class ApiFallbackRequester(object):

    INVALID_RESPONSE_STATUS_OFFSET = 400

    def __init__(self, hosts):
        from itertools import cycle
        self._hosts = list(hosts)
        self._hosts_cycle = cycle(self._hosts)
        self._current_host = next(self._hosts_cycle)
        self._request_id = 0

    def swap_url(self):
        self._current_host = next(self._hosts_cycle)

    def _bw_fetch(self, url, callback, headers, timeout, method, body):
        if isinstance(headers, dict):
            headers = tuple('{}: {}'.format(k, v) for k, v in headers.items() if v)
        return BigWorld.fetchURL(url, callback, headers, timeout, method, body or '')

    @wg_async
    def __call__(self, path, method='GET', headers=None, timeout=10.0, body=None, attempt=1):
        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'WoT-CalculationElo/1.3'
            }

        self._request_id += 1
        req_id = self._request_id
        current_host = str(self._current_host)
        url = current_host + path

        logger.debug('[Fetch #%s] attempt %s/%s  %s %s',
                     req_id, attempt, len(self._hosts), method, url)

        response = yield await_callback(self._bw_fetch)(
            url, headers=headers, timeout=timeout, method=method, body=body
        )

        status = getattr(response, 'responseCode', 0)
        logger.debug('[Fetch #%s] status=%s', req_id, status)

        if status < self.INVALID_RESPONSE_STATUS_OFFSET:
            raise AsyncReturn((status, getattr(response, 'body', '')))

        if attempt > len(self._hosts):
            logger.error('[Fetch #%s] All hosts exhausted', req_id)
            raise AsyncReturn((0, None))

        if current_host == self._current_host:
            self.swap_url()

        result = yield self(path, method, headers, timeout + 5.0, body, attempt + 1)
        raise AsyncReturn(result)


@wg_async
def fetch_data_with_retry(url, retries=2, delay=5, headers=None, method='GET',
                          postData='', timeout=30.0):
    if headers is None:
        headers = [
            ('Content-Type', 'application/json'),
            ('User-Agent', 'WoT-CalculationElo')
        ]

    lastError = None

    for attempt in range(1, retries + 1):
        try:
            logger.debug('[Fetch] Attempt %s/%s for URL: %s', attempt, retries, url)

            response = yield await_callback(_internal_fetch)(
                url, headers, timeout, method, postData
            )

            if not response:
                lastError = 'Empty response object'
                logger.error('[Fetch] Empty response on attempt %s/%s', attempt, retries)
                if attempt < retries:
                    yield _async_sleep(delay)
                continue

            responseBody = getattr(response, 'body', None) or (
                response.read() if hasattr(response, 'read') else str(response)
            )

            if not responseBody:
                lastError = 'Empty response body'
                logger.error('[Fetch] Empty body on attempt %s/%s', attempt, retries)
                if attempt < retries:
                    yield _async_sleep(delay)
                continue

            try:
                data = byteify(json.loads(responseBody))
                logger.debug('[Fetch] Success on attempt %s/%s', attempt, retries)
                raise AsyncReturn(data)
            except (ValueError, TypeError) as e:
                lastError = 'JSON decode error: {}'.format(e)
                logger.error('[Fetch] JSON error: %s', e)
                if attempt < retries:
                    yield _async_sleep(delay)

        except AsyncReturn:
            raise
        except Exception as e:
            lastError = str(e)
            logger.error('[Fetch] Error attempt %s/%s: %s', attempt, retries, e)
            if attempt < retries:
                yield _async_sleep(delay)

    logger.error('[Fetch] Failed after %s attempts. Last: %s', retries, lastError or 'Unknown')
    raise AsyncReturn(None)
