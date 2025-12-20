# -*- coding: utf-8 -*-
import json
import BigWorld
from wg_async import wg_async, AsyncReturn, await_callback

from .elo_changes import calculate_elo_changes

__all__ = [
    'print_log',
    'print_error',
    'print_debug',
    'fetch_data_with_retry',
    'calculate_elo_changes'
]

DEBUG_MODE = False


def print_log(log):
    print("[CalculationElo]: {}".format(str(log)))


def print_error(log):
    print("[CalculationElo] [ERROR]: {}".format(str(log)))


def print_debug(log):
    global DEBUG_MODE
    if DEBUG_MODE:
        print("[CalculationElo] [DEBUG]: {}".format(str(log)))


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
def fetch_data_with_retry(url, retries=2, delay=5, headers=None, method='GET', postData='', timeout=30.0):
    if headers is None:
        headers = [
            ('Content-Type', 'application/json'),
            ('User-Agent', 'WoT-Stats-Client/1.0')
        ]

    lastError = None

    for attempt in range(1, retries + 1):
        try:
            print_debug("[Fetch] Attempt {}/{} for URL: {}".format(attempt, retries, url))

            response = yield await_callback(_internal_fetch)(
                url,
                headers,
                timeout,
                method,
                postData
            )

            if not response:
                lastError = "Empty response object"
                print_error("[Fetch] Empty response on attempt {}/{}".format(attempt, retries))

                if attempt < retries:
                    print_debug("[Fetch] Retrying in {} seconds...".format(delay))
                    yield _async_sleep(delay)
                    continue

            if hasattr(response, 'body'):
                responseBody = response.body
            elif hasattr(response, 'read'):
                responseBody = response.read()
            else:
                responseBody = str(response)

            print_debug("[Fetch] Response type: {}, body length: {}".format(
                type(response).__name__,
                len(responseBody) if responseBody else 0
            ))

            if not responseBody:
                lastError = "Empty response body"
                print_error("[Fetch] Empty response body on attempt {}/{}".format(attempt, retries))

                if attempt < retries:
                    print_debug("[Fetch] Retrying in {} seconds...".format(delay))
                    yield _async_sleep(delay)
                    continue

            try:
                data = json.loads(responseBody)
                print_debug("[Fetch] Successfully fetched and parsed data on attempt {}/{}".format(
                    attempt, retries
                ))
                raise AsyncReturn(data)

            except (ValueError, TypeError) as e:
                lastError = "JSON decode error: {}".format(e)
                print_error("[Fetch] JSON decoding error: {}".format(e))
                print_error("[Fetch] Raw response (first 200 chars): {}".format(
                    responseBody[:200] if responseBody else 'None'
                ))

                if attempt < retries:
                    print_debug("[Fetch] Retrying in {} seconds...".format(delay))
                    yield _async_sleep(delay)
                    continue

        except AsyncReturn:
            raise

        except Exception as e:
            lastError = str(e)
            print_error("[Fetch] Unexpected error on attempt {}/{}: {}".format(attempt, retries, e))

            if '10054' in lastError:
                print_debug("[Fetch] Connection forcibly closed by server (error 10054)")
            elif 'timeout' in lastError.lower():
                print_debug("[Fetch] Request timeout")

            if DEBUG_MODE:
                import traceback
                print_error("[Fetch] Traceback: {}".format(traceback.format_exc()))

            if attempt < retries:
                print_debug("[Fetch] Retrying in {} seconds...".format(delay))
                yield _async_sleep(delay)

    print_error("[Fetch] Failed after {} attempts. Last error: {}".format(retries, lastError or 'Unknown'))
    raise AsyncReturn(None)


@wg_async
def _async_sleep(seconds):
    def dummyCallback():
        pass

    yield await_callback(BigWorld.callback)(seconds, dummyCallback)
