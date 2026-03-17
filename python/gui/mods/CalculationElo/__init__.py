# -*- coding: utf-8 -*-
from .utils import logger
from .battle_provider import BattleProvider
from .battle_state_events import g_battleStateEvents
from .clan import initialize_clan, finalize_clan, g_clan_state_manager
from .views import EloPanel, _registerFlashComponents, _unregisterFlashComponents
from .settings import g_config

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
        _registerFlashComponents()
        from .clan import g_clan_state_manager

        if g_elo_panel is None:
            g_elo_panel = EloPanel()
            g_elo_panel.setClanStateManager(g_clan_state_manager)

        if g_battle_provider is None:
            g_battle_provider = BattleProvider(g_clan_state_manager, g_elo_panel)

        logger.debug('[CalculationElo] All components initialized')

    except Exception as e:
        logger.error('[CalculationElo] Initialization failed: %s', e)
        import traceback
        logger.error('[CalculationElo] Traceback: %s', traceback.format_exc())
        finalize()


def finalize():
    global g_battle_provider, g_elo_panel
    try:
        _unregisterFlashComponents()
        if g_battle_provider:
            g_battle_provider.fini()
            g_battle_provider = None

        if g_elo_panel:
            g_elo_panel.destroy()
            g_elo_panel = None

        finalize_clan()
        g_config.fini()
        g_battleStateEvents.fini()

    except Exception as e:
        logger.error('[CalculationElo] Finalization failed: %s', e)
