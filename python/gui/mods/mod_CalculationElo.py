# -*- coding: utf-8 -*-
from CalculationElo.utils import logger
from CalculationElo import initialize, finalize

__version__ = '1.2.2'
__author__ = 'Under_Pressure'
__copyright__ = 'Copyright 2026, Under_Pressure'
__mod_name__ = 'Calculation_Elo'


def init():
    logger.debug('START LOADING: v%s', __version__)
    try:
        initialize()
        logger.info('LOADED SUCCESSFULLY: v%s', __version__)
    except Exception as e:
        logger.error('LOADING FAILED: %s', e)
        import traceback
        logger.error('Traceback: %s', traceback.format_exc())


def fini():
    logger.debug('SHUTTING DOWN: v%s', __version__)
    try:
        finalize()
        logger.info('SHUTDOWN COMPLETE: v%s', __version__)
    except Exception as e:
        logger.error('SHUTDOWN FAILED: %s', e)
