from CalculationElo.utils import *
from CalculationElo.arenaInfoProvider import ArenaInfoProvider

__version__ = "0.0.5" 
__author__ = "Under_Pressure"
__copyright__ = "Copyright 2025, Under_Pressure"
__mod_name__ = "Calculation_Elo"

g_arenaInfoProvider = None

def init():
    global g_arenaInfoProvider
    print_log('MOD START LOADING: v{}'. format(__version__))
    try:
        if g_arenaInfoProvider is not None:
            print_debug('Previous instance found, performing full cleanup...')
            try:
                g_arenaInfoProvider.fini()
            except Exception as e:
                print_error('Error cleaning previous instance: %s' % str(e))
            g_arenaInfoProvider = None
        
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
        
        try:
            from CalculationElo import g_multiTextPanel
            if g_multiTextPanel:
                g_multiTextPanel.force_cleanup()
                print_debug("Additional global cleanup completed")
        except Exception as e:
            print_error('Additional cleanup error: %s' % str(e))
            
        print_log('MOD SHUTDOWN COMPLETE: v{}'. format(__version__))
    except Exception as e:
        print_error('MOD SHUTDOWN ERROR: %s' % str(e))