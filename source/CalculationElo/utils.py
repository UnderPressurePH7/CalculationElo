import urllib2
import json
import time

DEBUG_MODE = True

def print_log(log):
    print("[CalculationElo]: {}".format(str(log)))


def print_error(log):
    print("[CalculationElo] [ERROR]: {}".format(str(log)))

def print_debug(log):
    global DEBUG_MODE
    if DEBUG_MODE:
        print("[CalculationElo] [DEBUG]: {}".format(str(log)))

def fetch_data_with_retry(url, retries=2, delay=5):
    for attempt in range(retries):
        try:
            response = urllib2.urlopen(url)
            data = response.read()
            return json.loads(data)
        except urllib2.URLError as e:
            print_error("URLError: {}, attempt {}/{}".format(e, attempt + 1, retries))
            if hasattr(e, 'reason') and '10054' in str(e.reason):
                print_debug("Connection forcibly closed by the server. Retrying...")
            time.sleep(delay)
        except ValueError as e:
            print_error("JSON decoding error: {}".format(e))
            break
        except Exception as e:
            print_error("Unexpected error: {}".format(e))
            break
    return None