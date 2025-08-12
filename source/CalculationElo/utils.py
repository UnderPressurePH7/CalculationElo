DEBUG_MODE = False

def print_log(log):
    print("[CalculationElo]: {}".format(str(log)))


def print_error(log):
    print("[CalculationElo] [ERROR]: {}".format(str(log)))

def print_debug(log):
    global DEBUG_MODE
    if DEBUG_MODE:
        print("[CalculationElo] [DEBUG]: {}".format(str(log)))
