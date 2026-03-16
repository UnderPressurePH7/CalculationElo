# -*- coding: utf-8 -*-
import BigWorld
import Keys
from gui import InputHandler
from gui.Scaleform.framework import g_entitiesFactories, ScopeTemplates, ViewSettings
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared.personality import ServicesLocator
from frameworks.wulf import WindowLayer

from ..battle_state_events import g_battleStateEvents
from ..settings import g_config
from ..settings.config_param import g_configParams, DisplayMode
from ..settings.translations import Translator
from ..utils import logger, weak_callback, cancelCallbackSafe

INJECTOR_LINKAGE = 'EloPanelInjector'
COMPONENT_LINKAGE = 'EloPanelMain'
SWF_PATH = 'EloPanelMain.swf'

BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080


def _registerFlashComponents():
    try:
        g_entitiesFactories.addSettings(
            ViewSettings(
                INJECTOR_LINKAGE, EloPanelInjectorView, SWF_PATH,
                WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE
            )
        )
        g_entitiesFactories.addSettings(
            ViewSettings(
                COMPONENT_LINKAGE, EloPanelView, None,
                WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE
            )
        )
        logger.debug('[EloPanel] Flash components registered')
    except Exception as e:
        logger.error('[EloPanel] Failed to register flash components: %s', e)


def _unregisterFlashComponents():
    try:
        g_entitiesFactories.removeSettings(INJECTOR_LINKAGE)
        g_entitiesFactories.removeSettings(COMPONENT_LINKAGE)
    except Exception:
        pass


class EloPanelInjectorView(View):

    _g_eloPanel = None

    def _populate(self):
        super(EloPanelInjectorView, self)._populate()
        logger.debug('[EloPanelInjectorView] _populate called')
        if EloPanelInjectorView._g_eloPanel:
            EloPanelInjectorView._g_eloPanel._onInjectorReady(self)

    def _dispose(self):
        logger.debug('[EloPanelInjectorView] _dispose called')
        if EloPanelInjectorView._g_eloPanel:
            EloPanelInjectorView._g_eloPanel._onInjectorDisposed()
        super(EloPanelInjectorView, self)._dispose()

    def py_onDragEnd(self, offset):
        logger.debug('[EloPanelInjectorView] py_onDragEnd offset=%s', offset)
        if EloPanelInjectorView._g_eloPanel:
            EloPanelInjectorView._g_eloPanel._onDragEnd(offset)


class EloPanelView(BaseDAAPIComponent):

    _g_eloPanel = None

    def __init__(self):
        super(EloPanelView, self).__init__()

    def _populate(self):
        super(EloPanelView, self)._populate()
        logger.debug('[EloPanelView] _populate called')
        if EloPanelView._g_eloPanel:
            EloPanelView._g_eloPanel._onFlashReady(self)
        else:
            logger.error('[EloPanelView] _populate: _g_eloPanel is None!')

    def _dispose(self):
        logger.debug('[EloPanelView] _dispose called')
        if EloPanelView._g_eloPanel:
            EloPanelView._g_eloPanel._onFlashDisposed()
        super(EloPanelView, self)._dispose()

    def as_updateState(self, alliesName, enemiesName, alliesRating, enemiesRating,
                       eloPlus, eloMinus, winsPercent, battlesCount):
        if self._isDAAPIInited():
            self.flashObject.as_updateState(alliesName, enemiesName, alliesRating, enemiesRating,
                                            eloPlus, eloMinus, winsPercent, battlesCount)

    def as_setVisible(self, isVisible):
        if self._isDAAPIInited():
            self.flashObject.as_setVisible(isVisible)

    def as_setPosition(self, offset):
        if self._isDAAPIInited():
            self.flashObject.as_setPosition(offset)

    def as_setScale(self, factor):
        if self._isDAAPIInited():
            self.flashObject.as_setScale(factor)

    def as_updateConfig(self, showTitle, showTeamNames, showEloChanges, showWinrateAndBattles,
                        headerText, headerColor, alliesNamesColor, enemiesNamesColor,
                        alliesRatingColor, enemiesRatingColor, eloGainColor, eloLossColor):
        if self._isDAAPIInited():
            self.flashObject.as_updateConfig(showTitle, showTeamNames, showEloChanges, showWinrateAndBattles,
                                             headerText, headerColor, alliesNamesColor, enemiesNamesColor,
                                             alliesRatingColor, enemiesRatingColor, eloGainColor, eloLossColor)


class EloPanel(object):
    def __init__(self):
        self._injectorView = None
        self._view = None
        self._flashReady = False
        self._isInitialized = False
        self._isVisible = False
        self._isHotkeyPressed = False
        self._activeKeys = {}
        self._clanStateManager = None

        self._pendingState = None

        self._currentState = {
            'allies_name': ' ',
            'enemies_name': ' ',
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0
        }

        self._offset = [
            g_configParams.panelPositionX.value,
            g_configParams.panelPositionY.value
        ]
        self._positionChanged = False
        self._saveCallbackId = None

        self._scaleFactor = 1.0
        self._screenWidth = BASE_SCREEN_WIDTH
        self._screenHeight = BASE_SCREEN_HEIGHT

    def setClanStateManager(self, manager):
        self._clanStateManager = manager
        if manager:
            manager.set_view(self)

    def onBattleStart(self):
        self._flashReady = False
        self._pendingState = None
        self._calculateScaleFactor()

        displayMode = g_configParams.displayMode.value
        self._isHotkeyPressed = (displayMode == DisplayMode.ALWAYS)

        EloPanelInjectorView._g_eloPanel = self
        EloPanelView._g_eloPanel = self

        if displayMode == DisplayMode.ON_HOTKEY_PRESSED:
            self._registerKeyHandlers()

        g_battleStateEvents.onGUIVisibility += self._onGUIVisibilityChanged
        g_battleStateEvents.onScaleChanged += self._onInterfaceScaleChanged
        g_battleStateEvents.onBattleClosed += self._onBattleClosed
        g_battleStateEvents.onBattleLoaded += self._onBattleLoaded
        g_config.onConfigChanged += self._onConfigChanged

        self._isInitialized = True
        logger.debug('[EloPanel] Battle started, displayMode=%s', displayMode)

    def _onBattleLoaded(self):
        try:
            g_battleStateEvents.onBattleLoaded -= self._onBattleLoaded
        except Exception:
            pass
        self._injectFlash()

    def _onBattleClosed(self):
        self.onBattleEnd()

    def onBattleEnd(self):
        try:
            g_battleStateEvents.onGUIVisibility -= self._onGUIVisibilityChanged
            g_battleStateEvents.onScaleChanged -= self._onInterfaceScaleChanged
            g_battleStateEvents.onBattleClosed -= self._onBattleClosed
            g_battleStateEvents.onBattleLoaded -= self._onBattleLoaded
        except Exception:
            pass

        try:
            g_config.onConfigChanged -= self._onConfigChanged
        except Exception:
            pass

        self._unregisterKeyHandlers()
        self._savePositionIfChanged()
        EloPanelInjectorView._g_eloPanel = None
        EloPanelView._g_eloPanel = None
        self._injectorView = None
        self._view = None
        self._flashReady = False
        self._resetState()
        self._isInitialized = False
        self._pendingState = None
        logger.debug('[EloPanel] Battle ended')

    def updateFromState(self, state):
        if not state:
            return

        self._currentState.update(state)

        if self._isInitialized:
            if self._flashReady and self._view:
                self._pushStateToFlash()
            else:
                self._pendingState = self._currentState.copy()

    def destroy(self):
        try:
            g_battleStateEvents.onGUIVisibility -= self._onGUIVisibilityChanged
            g_battleStateEvents.onScaleChanged -= self._onInterfaceScaleChanged
            g_battleStateEvents.onBattleClosed -= self._onBattleClosed
            g_battleStateEvents.onBattleLoaded -= self._onBattleLoaded
        except Exception:
            pass

        try:
            g_config.onConfigChanged -= self._onConfigChanged
        except Exception:
            pass

        self._unregisterKeyHandlers()
        self._savePositionIfChanged()
        EloPanelInjectorView._g_eloPanel = None
        EloPanelView._g_eloPanel = None
        self._injectorView = None
        self._view = None
        self._flashReady = False

        if self._clanStateManager:
            try:
                self._clanStateManager.set_view(None)
            except Exception:
                pass
            self._clanStateManager = None

    def _injectFlash(self):
        try:
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app:
                app.loadView(SFViewLoadParams(INJECTOR_LINKAGE))
                logger.debug('[EloPanel] Injector SWF loaded')
            else:
                logger.error('[EloPanel] Battle app not available')
        except Exception as e:
            logger.error('[EloPanel] Failed to inject flash: %s', e)

    def _onInjectorReady(self, injectorView):
        self._injectorView = injectorView
        logger.debug('[EloPanel] Injector view ready')

    def _onInjectorDisposed(self):
        self._injectorView = None
        logger.debug('[EloPanel] Injector view disposed')

    def _onFlashReady(self, view):
        self._view = view
        self._flashReady = True
        logger.debug('[EloPanel] Flash component ready, pushing config/state')

        self._pushConfigToFlash()
        self._view.as_setScale(self._scaleFactor)
        self._view.as_setPosition(self._offset)

        self._view.as_setVisible(self._isHotkeyPressed)
        self._isVisible = self._isHotkeyPressed

        if self._pendingState:
            self._currentState.update(self._pendingState)
            self._pendingState = None

        self._pushStateToFlash()

    def _onFlashDisposed(self):
        self._view = None
        self._flashReady = False
        logger.debug('[EloPanel] Flash component disposed')

    def _onConfigChanged(self):
        logger.debug('[EloPanel] Config changed, refreshing flash')
        if self._flashReady and self._view:
            self._pushConfigToFlash()

    def _pushStateToFlash(self):
        if not self._view or not self._flashReady:
            return

        s = self._currentState
        self._view.as_updateState(
            s.get('allies_name', ' '),
            s.get('enemies_name', ' '),
            s.get('allies_rating', 0),
            s.get('enemies_rating', 0),
            s.get('elo_plus', 0),
            s.get('elo_minus', 0),
            s.get('wins_percent', 0),
            s.get('battles_count', 0)
        )

    def _pushConfigToFlash(self):
        if not self._view or not self._flashReady:
            return

        headerText = Translator.MOD_NAME
        if not isinstance(headerText, str):
            try:
                headerText = str(headerText)
            except Exception:
                headerText = 'ELO Calculator'

        self._view.as_updateConfig(
            g_configParams.showTitleVisible.value,
            g_configParams.showTeamNames.value,
            g_configParams.showEloChanges.value,
            g_configParams.showWinrateAndBattles.value,
            headerText,
            g_configParams.headerColor.getPackedColor(),
            g_configParams.alliesNamesColor.getPackedColor(),
            g_configParams.enemiesNamesColor.getPackedColor(),
            g_configParams.alliesRatingColor.getPackedColor(),
            g_configParams.enemiesRatingColor.getPackedColor(),
            g_configParams.eloGainColor.getPackedColor(),
            g_configParams.eloLossColor.getPackedColor()
        )

    def _onDragEnd(self, offset):
        try:
            self._offset = [int(offset[0]), int(offset[1])]
            self._positionChanged = True
            self._scheduleSavePosition()
            logger.debug('[EloPanel] Drag end: offset=(%s, %s)', offset[0], offset[1])
        except Exception as e:
            logger.error('[EloPanel] Error processing drag end: %s', e)

    def _onGUIVisibilityChanged(self, isVisible):
        if not self._isInitialized or not self._view:
            return

        if self._isHotkeyPressed:
            self._updateVisibility(isVisible)

    def _onInterfaceScaleChanged(self, scale):
        if not self._isInitialized or not self._view:
            return

        self._calculateScaleFactor()

        if self._flashReady:
            self._view.as_setScale(self._scaleFactor)

    def _calculateScaleFactor(self):
        try:
            self._screenWidth = BigWorld.screenWidth()
            self._screenHeight = BigWorld.screenHeight()

            if self._screenWidth <= 0 or self._screenHeight <= 0:
                self._screenWidth = BASE_SCREEN_WIDTH
                self._screenHeight = BASE_SCREEN_HEIGHT

            interfaceScale = g_battleStateEvents.interfaceScale
            self._scaleFactor = interfaceScale if interfaceScale and interfaceScale > 0 else 1.0

        except Exception as e:
            logger.error('[EloPanel] Error calculating scale factor: %s', e)
            self._scaleFactor = 1.0

    def _updateVisibility(self, isVisible):
        self._isVisible = isVisible
        if self._view and self._flashReady:
            self._view.as_setVisible(isVisible)

    def _scheduleSavePosition(self):
        cancelCallbackSafe(self._saveCallbackId)
        self._saveCallbackId = None
        self._saveCallbackId = BigWorld.callback(
            2.0, weak_callback(self, '_deferredSavePosition')
        )

    def _deferredSavePosition(self):
        self._saveCallbackId = None
        self._savePositionIfChanged()

    def _savePositionIfChanged(self):
        cancelCallbackSafe(self._saveCallbackId)
        self._saveCallbackId = None

        if not self._positionChanged:
            return

        g_configParams.panelPositionX.value = self._offset[0]
        g_configParams.panelPositionY.value = self._offset[1]
        g_config.configFile.save_config()

        self._positionChanged = False
        logger.debug('[EloPanel] Position saved: offset=(%s, %s)', self._offset[0], self._offset[1])

    def _registerKeyHandlers(self):
        try:
            InputHandler.g_instance.onKeyDown += self._onKeyDown
            InputHandler.g_instance.onKeyUp += self._onKeyUp
        except Exception as e:
            logger.error('[EloPanel] Failed to register key handlers: %s', e)

    def _unregisterKeyHandlers(self):
        try:
            InputHandler.g_instance.onKeyDown -= self._onKeyDown
            InputHandler.g_instance.onKeyUp -= self._onKeyUp
        except Exception:
            pass

    def _onKeyDown(self, event):
        hotkeys = g_configParams.eloHotKey.value
        if not hotkeys:
            return

        for key in hotkeys:
            if event.key == key and not self._activeKeys.get(key, False):
                self._activeKeys[key] = True
                break

        if all(self._activeKeys.get(key, False) for key in hotkeys):
            if not self._isHotkeyPressed:
                self._isHotkeyPressed = True
                self._updateVisibility(g_battleStateEvents.visible)

    def _onKeyUp(self, event):
        hotkeys = g_configParams.eloHotKey.value
        if not hotkeys:
            return

        for key in hotkeys:
            if event.key == key and self._activeKeys.get(key, False):
                self._activeKeys[key] = False
                break

        if not any(self._activeKeys.get(key, False) for key in hotkeys):
            if self._isHotkeyPressed:
                self._isHotkeyPressed = False
                self._updateVisibility(False)

    def _resetState(self):
        self._currentState = {
            'allies_name': ' ',
            'enemies_name': ' ',
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0
        }
        self._isHotkeyPressed = False
        self._activeKeys = {}
        self._pendingState = None