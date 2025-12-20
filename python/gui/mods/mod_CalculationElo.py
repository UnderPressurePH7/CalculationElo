# -*- coding: utf-8 -*-
from CalculationElo.utils import print_log, print_debug
from CalculationElo import initialize, finalize

__version__ = "1.1.0"
__author__ = "Under_Pressure"
__copyright__ = "Copyright 2025, Under_Pressure"
__mod_name__ = "Calculation_Elo"


def init():
    print_log('START LOADING: v{}'.format(__version__))
    try:
        initialize()
        print_log('LOADED SUCCESSFULLY: v{}'.format(__version__))
    except Exception as e:
        print_log('LOADING FAILED: {}'.format(str(e)))
        import traceback
        print_log('Traceback: {}'.format(traceback.format_exc()))


def fini():
    print_log('SHUTTING DOWN: v{}'.format(__version__))
    try:
        finalize()
        print_log('SHUTDOWN COMPLETE: v{}'.format(__version__))
    except Exception as e:
        print_log('SHUTDOWN FAILED: {}'.format(str(e)))