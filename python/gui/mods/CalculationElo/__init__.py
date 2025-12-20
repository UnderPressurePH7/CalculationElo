# -*- coding: utf-8 -*-
from .utils import print_error, print_debug
from .battle_provider import BattleProvider
from .clan import initialize_clan, finalize_clan, g_clan_state_manager
from .views import EloPanel

__all__ = [
    'initialize',
    'finalize'
]

g_battle_provider = None
g_elo_panel = None


def initialize():
    global g_battle_provider, g_elo_panel
    try:
        initialize_clan()
        
        from .clan import g_clan_state_manager
        
        if g_elo_panel is None:
            g_elo_panel = EloPanel()
            g_elo_panel.setClanStateManager(g_clan_state_manager)
            print_debug("[EloPanel] Initialized")
        
        if g_battle_provider is None:
            g_battle_provider = BattleProvider(g_clan_state_manager, g_elo_panel)
            print_debug("[BattleProvider] Initialized")
        
        print_debug("[CalculationElo] All components initialized successfully")
        
    except Exception as e:
        print_error("[CalculationElo] Initialization failed: {}".format(str(e)))
        import traceback
        print_error("[CalculationElo] Traceback: {}".format(traceback.format_exc()))
        finalize()


def finalize():
    global g_battle_provider, g_elo_panel
    try:
        if g_battle_provider:
            g_battle_provider.fini()
            g_battle_provider = None
            print_debug("[BattleProvider] Finalized")
        
        if g_elo_panel:
            g_elo_panel.destroy()
            g_elo_panel = None
            print_debug("[EloPanel] Finalized")
        
        finalize_clan()
        
        print_debug("[CalculationElo] All components finalized successfully")
        
    except Exception as e:
        print_error("[CalculationElo] Finalization failed: {}".format(str(e)))