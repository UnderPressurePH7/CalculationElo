DEBUG_MODE = True

def print_log(log):
    print("[MOD_CALC_ELO]: {}".format(str(log)))


def print_error(log):
    print("[MOD_CALC_ELO_ERROR]: {}".format(str(log)))


def print_debug(log):
    global DEBUG_MODE
    if DEBUG_MODE:
        print("[MOD_CALC_ELO_DEBUG]: {}".format(str(log)))

