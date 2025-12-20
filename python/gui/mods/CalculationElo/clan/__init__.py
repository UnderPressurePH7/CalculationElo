# -*- coding: utf-8 -*-
from ..utils import print_error, print_debug
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
            print_debug("[ClanAPI] Initialized")

        if g_clan_state_manager is None:
            g_clan_state_manager = ClanStateManager(g_clan_api)
            print_debug("[ClanStateManager] Initialized")

        print_debug("[CalculationElo] Clan components initialized successfully")

    except Exception as e:
        print_error("[CalculationElo] Clan initialization failed: {}".format(str(e)))


def finalize_clan():
    global g_clan_api, g_clan_state_manager
    try:
        if g_clan_state_manager:
            g_clan_state_manager.reset_state()
            g_clan_state_manager = None
            print_debug("[ClanStateManager] Finalized")

        if g_clan_api:
            g_clan_api.fini()
            g_clan_api = None
            print_debug("[ClanAPI] Finalized")

        print_debug("[CalculationElo] Clan components finalized successfully")

    except Exception as e:
        print_error("[CalculationElo] Clan finalization failed: {}".format(str(e)))
