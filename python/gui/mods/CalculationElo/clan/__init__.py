# -*- coding: utf-8 -*-
from ..utils import logger
from .clan_api import ClanAPI
from .clan_state_manager import ClanStateManager

__all__ = [
    'initialize_clan',
    'finalize_clan',
    'g_clan_state_manager',
    'g_clan_api'
]

g_clan_api = None
g_clan_state_manager = None


def initialize_clan():
    global g_clan_api, g_clan_state_manager
    try:
        if g_clan_api is None:
            g_clan_api = ClanAPI()
            logger.debug('[ClanAPI] Initialized')

        if g_clan_state_manager is None:
            g_clan_state_manager = ClanStateManager(g_clan_api)
            logger.debug('[ClanStateManager] Initialized')

    except Exception as e:
        logger.error('[CalculationElo] Clan initialization failed: %s', e)


def finalize_clan():
    global g_clan_api, g_clan_state_manager
    try:
        if g_clan_state_manager:
            g_clan_state_manager.reset_state()
            g_clan_state_manager = None

        if g_clan_api:
            g_clan_api.fini()
            g_clan_api = None

    except Exception as e:
        logger.error('[CalculationElo] Clan finalization failed: %s', e)
