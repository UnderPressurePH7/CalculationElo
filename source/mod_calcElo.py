from CalculationElo.utils import *
from CalculationElo.arenaInfoProvider import ArenaInfoProvider
from CalculationElo.config import g_config

__version__ = "0.0.4"
__author__ = "Under_Pressure"
__copyright__ = "Copyright 2025, Under_Pressure"
__mod_name__ = "Calculation_Elo"

g_arenaInfoProvider = None

def init():
    global g_arenaInfoProvider
    
    try:
        print_log('MOD START LOADING: v{}'.format(__version__))
        print_debug('Initializing Calculation ELO mod...')

        if g_config is None:
            print_error('Config not initialized! Mod may not work correctly.')
        else:
            print_debug('Config initialized successfully')

        g_arenaInfoProvider = ArenaInfoProvider()
        
        print_log('MOD LOADED SUCCESSFULLY: v{}'.format(__version__))
        
    except Exception as e:
        print_error('Error during mod initialization: %s' % str(e))
        print_error('Mod may not work correctly!')

def fini():
    global g_arenaInfoProvider
    
    try:
        print_log('MOD SHUTTING DOWN: v{}'.format(__version__))
        
        if g_arenaInfoProvider:
            g_arenaInfoProvider.fini()
            g_arenaInfoProvider = None
            print_debug('ArenaInfoProvider finalized')
        
        print_log('MOD SHUTDOWN COMPLETE: v{}'.format(__version__))
        
    except Exception as e:
        print_error('Error during mod shutdown: %s' % str(e))
    
    finally:
        g_arenaInfoProvider = None