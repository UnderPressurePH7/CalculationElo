from CalculationElo.utils import *
from CalculationElo.arenaInfoProvider import ArenaInfoProvider

__version__ = "0.0.4"
__author__ = "Under_Pressure"
__copyright__ = "Copyright 2025, Under_Pressure"
__mod_name__ = "Calculation_Elo"

g_arenaInfoProvider = None

def init():
    global g_arenaInfoProvider
    print_log('MOD START LOADING: v{}'. format(__version__))
    try:
        g_arenaInfoProvider = ArenaInfoProvider()
        print_log('MOD LOADED SUCCESSFULLY: v{}'. format(__version__))
    except Exception as e:
        print_error('MOD FAILED TO LOAD: %s' % str(e))

def fini():
    global g_arenaInfoProvider
    print_log('MOD SHUTTING DOWN: v{}'. format(__version__))
    try:
        if g_arenaInfoProvider is not None:
            g_arenaInfoProvider.fini()
            g_arenaInfoProvider = None
        print_log('MOD SHUTDOWN COMPLETE: v{}'. format(__version__))
    except Exception as e:
        print_error('MOD SHUTDOWN ERROR: %s' % str(e))