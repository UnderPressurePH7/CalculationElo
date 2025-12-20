# -*- coding: utf-8 -*-
import BigWorld
import Keys
from gui import InputHandler
from gui.shared import g_eventBus, events

from ..settings import g_config
from ..settings.config_param import g_configParams, DisplayMode
from ..utils import print_debug, print_error

try:
    from gui.mods.gambiter import g_guiFlash
    from gui.mods.gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, g_guiCache, COMPONENT_EVENT
    HAS_GUIFLASH = g_guiFlash is not None
except ImportError:
    print_error("[EloPanel] GUIFlash not found! Install gui.mods.gambiter")
    HAS_GUIFLASH = False
    g_guiFlash = None
    g_guiCache = None
    COMPONENT_EVENT = None
    COMPONENT_TYPE = None
    COMPONENT_ALIGN = None


PANEL_ALIAS = 'eloPanelMain'

BASE_SCREEN_WIDTH = 1920
BASE_PANEL_WIDTH = 140
BASE_PANEL_HEIGHT = 110

BACKGROUND_IMAGE = 'img://gui/maps/icons/tanksetup/popular_loadouts/legendary_bg.png'


class EloPanelComponents:
    BACKGROUND = 'eloPanelMain.background'
    HEADER = 'eloPanelMain.headerLabel'
    ALLIES_NAME = 'eloPanelMain.alliesNameLabel'
    ENEMIES_NAME = 'eloPanelMain.enemiesNameLabel'
    ALLIES_RATING = 'eloPanelMain.alliesRatingLabel'
    ENEMIES_RATING = 'eloPanelMain.enemiesRatingLabel'
    ELO_GAIN = 'eloPanelMain.eloGainLabel'
    ELO_LOSS = 'eloPanelMain.eloLossLabel'
    ENEMY_STATS = 'eloPanelMain.enemyStatsLabel'

    @classmethod
    def all(cls):
        return [
            cls.BACKGROUND,
            cls.HEADER,
            cls.ALLIES_NAME,
            cls.ENEMIES_NAME,
            cls.ALLIES_RATING,
            cls.ENEMIES_RATING,
            cls.ELO_GAIN,
            cls.ELO_LOSS,
            cls.ENEMY_STATS
        ]


class EloPanel(object):

    def __init__(self):
        self._isInitialized = False
        self._isVisible = False
        self._isHotkeyPressed = False
        self._activeKeys = {}
        self._clanStateManager = None
        self._hasGuiFlash = HAS_GUIFLASH

        self._currentState = {
            'allies_name': '---',
            'enemies_name': '---',
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0
        }

        self._panelX = g_configParams.panelPositionX.value
        self._panelY = g_configParams.panelPositionY.value
        self._positionChanged = False
        self._saveCallbackId = None

        self._scaleFactor = 1.0
        self._panelWidth = BASE_PANEL_WIDTH
        self._panelHeight = BASE_PANEL_HEIGHT
        self._screenWidth = BASE_SCREEN_WIDTH
        self._screenHeight = 1080

        if self._hasGuiFlash and COMPONENT_EVENT:
            COMPONENT_EVENT.UPDATED += self._onComponentUpdated

        print_debug("[EloPanel] Initialized (GUIFlash: {})".format(self._hasGuiFlash))

    def _calculateScaleFactor(self):
        try:
            self._screenWidth = BigWorld.screenWidth()
            self._screenHeight = BigWorld.screenHeight()
            
            print_debug("[EloPanel] Screen resolution: {}x{}".format(self._screenWidth, self._screenHeight))
            
            if self._screenWidth < BASE_SCREEN_WIDTH:
                self._scaleFactor = 0.85
            elif self._screenWidth > BASE_SCREEN_WIDTH:
                self._scaleFactor = 1.3
            else:
                self._scaleFactor = 1.0
            
            self._panelWidth = int(BASE_PANEL_WIDTH * self._scaleFactor)
            self._panelHeight = int(BASE_PANEL_HEIGHT * self._scaleFactor)
            
            print_debug("[EloPanel] Scale factor: {}, Panel size: {}x{}".format(
                self._scaleFactor, self._panelWidth, self._panelHeight))
            
        except Exception as e:
            print_error("[EloPanel] Error calculating scale factor: {}".format(e))
            self._scaleFactor = 1.0
            self._panelWidth = BASE_PANEL_WIDTH
            self._panelHeight = BASE_PANEL_HEIGHT

    def _scaled(self, value):
        return int(value * self._scaleFactor)

    def _scaledFloat(self, value):
        """Масштабує значення з плаваючою точкою"""
        return value * self._scaleFactor

    def setClanStateManager(self, manager):
        self._clanStateManager = manager
        if manager:
            manager.set_view(self)
        print_debug("[EloPanel] ClanStateManager set: {}".format(manager is not None))

    def onBattleStart(self):
        print_debug("[EloPanel] Battle started")

        if not self._hasGuiFlash:
            print_error("[EloPanel] GUIFlash not available - panel disabled")
            return

        self._calculateScaleFactor()

        displayMode = g_configParams.displayMode.value
        self._isHotkeyPressed = (displayMode == DisplayMode.ALWAYS)

        self._createPanel()
        self._createBackground()
        self._createLabels()
        self._updateVisibility(self._isHotkeyPressed)

        if displayMode == DisplayMode.ON_HOTKEY_PRESSED:
            self._registerKeyHandlers()

        self._isInitialized = True

    def onBattleEnd(self):
        print_debug("[EloPanel] Battle ended")

        self._unregisterKeyHandlers()
        self._savePositionIfChanged()
        self._deleteAllComponents()
        self._resetState()

        self._isInitialized = False

    def updateFromState(self, state):
        if not state:
            return
        
        self._currentState.update(state)
        
        if self._isInitialized:
            self._refreshLabels()

    def _createPanel(self):
        if not self._hasGuiFlash or not g_guiCache:
            return

        if g_guiCache.isComponent(PANEL_ALIAS):
            print_debug("[EloPanel] Panel already exists")
            return

        # Масштабуємо позицію панелі відносно роздільної здатності
        scaledX = int(self._panelX * self._screenWidth / BASE_SCREEN_WIDTH)
        scaledY = int(self._panelY * self._screenHeight / 1080)

        panelConfig = {
            'x': scaledX,
            'y': scaledY,
            'width': self._panelWidth,
            'height': self._panelHeight,
            'drag': True,
            'limit': True,
            'border': False,
            'alignX': COMPONENT_ALIGN.LEFT,
            'alignY': COMPONENT_ALIGN.TOP,
            'visible': False
        }

        g_guiFlash.createComponent(PANEL_ALIAS, COMPONENT_TYPE.PANEL, panelConfig)
        print_debug("[EloPanel] Panel created at ({}, {}) with size {}x{}".format(
            scaledX, scaledY, self._panelWidth, self._panelHeight))

    def _createBackground(self):
        if not self._hasGuiFlash or not g_guiCache:
            return

        if g_guiCache.isComponent(EloPanelComponents.BACKGROUND):
            return

        bgConfig = {
            'image': BACKGROUND_IMAGE,
            'x': 0,
            'y': 0,
            'width': self._panelWidth,
            'height': self._panelHeight,
            'alpha': 0.85,
            'visible': False
        }

        g_guiFlash.createComponent(EloPanelComponents.BACKGROUND, COMPONENT_TYPE.IMAGE, bgConfig)
        print_debug("[EloPanel] Background created with size {}x{}".format(
            self._panelWidth, self._panelHeight))

    def _createLabels(self):
        if not self._hasGuiFlash or not g_guiCache:
            return

        if not g_guiCache.isComponent(PANEL_ALIAS):
            print_error("[EloPanel] Cannot create labels - panel not found")
            return

        shadowConfig = self._getShadowConfig()
        currentY = self._scaled(5)

        if g_configParams.showTitleVisible.value:
            self._createLabel(
                EloPanelComponents.HEADER,
                self._formatText("ELO Calculator", self._scaled(14), g_configParams.headerColor.getHexColor()),
                x=0, y=currentY,
                alignX=COMPONENT_ALIGN.CENTER,
                shadow=shadowConfig
            )
            currentY += self._scaled(22)

        if g_configParams.showTeamNames.value:
            alliesColor = g_configParams.alliesNamesColor.getHexColor()
            enemiesColor = g_configParams.enemiesNamesColor.getHexColor()

            self._createLabel(
                EloPanelComponents.ALLIES_NAME,
                self._formatText("---", self._scaled(16), alliesColor),
                x=self._scaled(5), y=currentY,
                alignX=COMPONENT_ALIGN.LEFT,
                shadow=shadowConfig
            )

            self._createLabel(
                EloPanelComponents.ENEMIES_NAME,
                self._formatText("---", self._scaled(16), enemiesColor),
                x=-self._scaled(5), y=currentY,
                alignX=COMPONENT_ALIGN.RIGHT,
                shadow=shadowConfig
            )
            currentY += self._scaled(22)

        alliesRatingColor = g_configParams.alliesRatingColor.getHexColor()
        enemiesRatingColor = g_configParams.enemiesRatingColor.getHexColor()

        self._createLabel(
            EloPanelComponents.ALLIES_RATING,
            self._formatText("---", self._scaled(20), alliesRatingColor),
            x=self._scaled(15), y=currentY,
            alignX=COMPONENT_ALIGN.LEFT,
            shadow=shadowConfig
        )

        self._createLabel(
            EloPanelComponents.ENEMIES_RATING,
            self._formatText("---", self._scaled(20), enemiesRatingColor),
            x=-self._scaled(15), y=currentY,
            alignX=COMPONENT_ALIGN.RIGHT,
            shadow=shadowConfig
        )
        currentY += self._scaled(24)

        if g_configParams.showEloChanges.value:
            eloGainColor = g_configParams.eloGainColor.getHexColor()
            eloLossColor = g_configParams.eloLossColor.getHexColor()

            self._createLabel(
                EloPanelComponents.ELO_GAIN,
                self._formatText("", self._scaled(14), eloGainColor),
                x=self._scaled(20), y=currentY,
                alignX=COMPONENT_ALIGN.LEFT,
                shadow=shadowConfig
            )

            self._createLabel(
                EloPanelComponents.ELO_LOSS,
                self._formatText("", self._scaled(14), eloLossColor),
                x=-self._scaled(20), y=currentY,
                alignX=COMPONENT_ALIGN.RIGHT,
                shadow=shadowConfig
            )
            currentY += self._scaled(18)

        if g_configParams.showWinrateAndBattles.value:
            self._createLabel(
                EloPanelComponents.ENEMY_STATS,
                self._formatText("", self._scaled(14), "#FFFFFF"),
                x=0, y=currentY,
                alignX=COMPONENT_ALIGN.CENTER,
                shadow=shadowConfig
            )

        print_debug("[EloPanel] Labels created with scale factor {}".format(self._scaleFactor))

    def _createLabel(self, alias, text, x, y, alignX, shadow=None):
        if not self._hasGuiFlash or not g_guiCache:
            return

        if g_guiCache.isComponent(alias):
            return

        labelConfig = {
            'text': text,
            'x': x,
            'y': y,
            'alignX': alignX,
            'isHtml': True,
            'visible': False
        }

        if shadow:
            labelConfig['shadow'] = shadow

        g_guiFlash.createComponent(alias, COMPONENT_TYPE.LABEL, labelConfig)

    def _refreshLabels(self):
        shadowConfig = self._getShadowConfig()
        state = self._currentState

        if g_configParams.showTeamNames.value:
            alliesColor = g_configParams.alliesNamesColor.getHexColor()
            enemiesColor = g_configParams.enemiesNamesColor.getHexColor()
            
            alliesName = state.get('allies_name', '---')
            enemiesName = state.get('enemies_name', '---')
            
            alliesDisplay = self._truncateName(alliesName) if alliesName and alliesName != 'Unknown' else '---'
            enemiesDisplay = self._truncateName(enemiesName) if enemiesName and enemiesName != 'Unknown' else '---'

            self._updateLabel(
                EloPanelComponents.ALLIES_NAME,
                self._formatText(alliesDisplay, self._scaled(16), alliesColor),
                shadowConfig
            )
            self._updateLabel(
                EloPanelComponents.ENEMIES_NAME,
                self._formatText(enemiesDisplay, self._scaled(16), enemiesColor),
                shadowConfig
            )

        alliesRatingColor = g_configParams.alliesRatingColor.getHexColor()
        enemiesRatingColor = g_configParams.enemiesRatingColor.getHexColor()

        alliesRating = state.get('allies_rating', 0)
        enemiesRating = state.get('enemies_rating', 0)

        self._updateLabel(
            EloPanelComponents.ALLIES_RATING,
            self._formatText(str(alliesRating) if alliesRating > 0 else '---', self._scaled(20), alliesRatingColor),
            shadowConfig
        )
        self._updateLabel(
            EloPanelComponents.ENEMIES_RATING,
            self._formatText(str(enemiesRating) if enemiesRating > 0 else '---', self._scaled(20), enemiesRatingColor),
            shadowConfig
        )

        if g_configParams.showEloChanges.value:
            eloGainColor = g_configParams.eloGainColor.getHexColor()
            eloLossColor = g_configParams.eloLossColor.getHexColor()

            eloPlus = state.get('elo_plus', 0)
            eloMinus = state.get('elo_minus', 0)

            self._updateLabel(
                EloPanelComponents.ELO_GAIN,
                self._formatText("+{}".format(eloPlus) if eloPlus > 0 else '', self._scaled(14), eloGainColor),
                shadowConfig
            )
            self._updateLabel(
                EloPanelComponents.ELO_LOSS,
                self._formatText(str(eloMinus) if eloMinus < 0 else '', self._scaled(14), eloLossColor),
                shadowConfig
            )

        if g_configParams.showWinrateAndBattles.value:
            winsPercent = state.get('wins_percent', 0)
            battlesCount = state.get('battles_count', 0)

            statsText = self._buildStatsText(battlesCount, winsPercent)
            self._updateLabel(EloPanelComponents.ENEMY_STATS, statsText, shadowConfig)

    def _updateLabel(self, alias, text, shadow=None, visible=None):
        if not self._hasGuiFlash or not g_guiCache:
            return

        if not g_guiCache.isComponent(alias):
            return

        updateConfig = {'text': text}

        if shadow:
            updateConfig['shadow'] = shadow

        if visible is not None:
            updateConfig['visible'] = visible

        g_guiFlash.updateComponent(alias, updateConfig)

    def _buildStatsText(self, battlesCount, winsPercent):
        if battlesCount <= 0 and winsPercent <= 0:
            return ''

        battlesColor = self._getBattlesColor(battlesCount)
        winrateColor = self._getWinrateColor(winsPercent)

        scaledSize = self._scaled(14)
        parts = []
        if battlesCount > 0:
            parts.append('<font face="Tahoma" size="{}" color="{}"><b>{}</b></font>'.format(
                scaledSize, battlesColor, battlesCount
            ))
        if winsPercent > 0:
            parts.append('<font face="Tahoma" size="{}" color="{}"><b>({}%)</b></font>'.format(
                scaledSize, winrateColor, winsPercent
            ))

        return ' '.join(parts)

    def _getWinrateColor(self, winrate):
        if winrate < 47:
            return "#FE0E00"
        elif winrate < 49:
            return "#FE7903"
        elif winrate < 52:
            return "#F8F400"
        elif winrate < 57:
            return "#60FF00"
        elif winrate < 64:
            return "#02C9B3"
        else:
            return "#D042F3"

    def _getBattlesColor(self, battles):
        if battles < 50:
            return "#AAAAAA"
        elif battles < 100:
            return "#FFFFFF"
        else:
            return "#60FF00"

    def _truncateName(self, name, maxLength=6):
        if not name:
            return '---'
        return name[:maxLength].upper() if len(name) > maxLength else name.upper()

    def _formatText(self, text, size, color):
        return '<font face="Tahoma" size="{}" color="{}"><b>{}</b></font>'.format(size, color, text)

    def _getShadowConfig(self):
        return {
            'distance': self._scaled(1),
            'angle': 45,
            'color': 0x000000,
            'alpha': 0.7,
            'blurX': self._scaled(2),
            'blurY': self._scaled(2),
            'strength': 1,
            'quality': 1
        }

    def _updateVisibility(self, isVisible):
        if not self._hasGuiFlash or not g_guiCache:
            return

        self._isVisible = isVisible

        if g_guiCache.isComponent(PANEL_ALIAS):
            g_guiFlash.updateComponent(PANEL_ALIAS, {'visible': isVisible})

        for alias in EloPanelComponents.all():
            if g_guiCache.isComponent(alias):
                g_guiFlash.updateComponent(alias, {'visible': isVisible})

    def _hideAllComponents(self):
        self._updateVisibility(False)

    def _deleteAllComponents(self):
        if not self._hasGuiFlash or not g_guiCache:
            return

        for alias in EloPanelComponents.all():
            if g_guiCache.isComponent(alias):
                try:
                    g_guiFlash.deleteComponent(alias)
                except Exception as e:
                    print_debug("[EloPanel] Failed to delete {}: {}".format(alias, e))

        if g_guiCache.isComponent(PANEL_ALIAS):
            try:
                g_guiFlash.deleteComponent(PANEL_ALIAS)
            except Exception as e:
                print_debug("[EloPanel] Failed to delete panel: {}".format(e))

        print_debug("[EloPanel] All components deleted")

    def _onComponentUpdated(self, alias, props):
        if alias != PANEL_ALIAS:
            return

        newX = props.get('x')
        newY = props.get('y')

        if newX is not None and newY is not None:
            baseX = int(newX * BASE_SCREEN_WIDTH / self._screenWidth)
            baseY = int(newY * 1080 / self._screenHeight)
            
            if baseX != self._panelX or baseY != self._panelY:
                self._panelX = max(0, min(baseX, BASE_SCREEN_WIDTH - BASE_PANEL_WIDTH))
                self._panelY = max(0, min(baseY, 1080 - BASE_PANEL_HEIGHT))
                self._positionChanged = True
                self._scheduleSavePosition()
                print_debug("[EloPanel] Position changed to ({}, {}) [base coords]".format(
                    self._panelX, self._panelY))

    def _scheduleSavePosition(self):
        if self._saveCallbackId:
            BigWorld.cancelCallback(self._saveCallbackId)
        self._saveCallbackId = BigWorld.callback(2.0, self._savePositionIfChanged)

    def _savePositionIfChanged(self):
        self._saveCallbackId = None
        
        if not self._positionChanged:
            return

        g_configParams.panelPositionX.value = self._panelX
        g_configParams.panelPositionY.value = self._panelY
        g_config.configFile.save_config()
        
        self._positionChanged = False
        print_debug("[EloPanel] Position saved: ({}, {})".format(self._panelX, self._panelY))

    def _registerKeyHandlers(self):
        try:
            InputHandler.g_instance.onKeyDown += self._onKeyDown
            InputHandler.g_instance.onKeyUp += self._onKeyUp
            print_debug("[EloPanel] Key handlers registered")
        except Exception as e:
            print_error("[EloPanel] Failed to register key handlers: {}".format(e))

    def _unregisterKeyHandlers(self):
        try:
            InputHandler.g_instance.onKeyDown -= self._onKeyDown
            InputHandler.g_instance.onKeyUp -= self._onKeyUp
            print_debug("[EloPanel] Key handlers unregistered")
        except Exception as e:
            print_debug("[EloPanel] Key handlers already unregistered: {}".format(e))

    def _onKeyDown(self, event):
        hotkeys = g_configParams.eloHotKey.value
        
        for key in hotkeys:
            if event.key == key and not self._activeKeys.get(key, False):
                self._activeKeys[key] = True
                break

        if all(self._activeKeys.get(key, False) for key in hotkeys):
            if not self._isHotkeyPressed:
                self._isHotkeyPressed = True
                self._updateVisibility(True)

    def _onKeyUp(self, event):
        hotkeys = g_configParams.eloHotKey.value
        
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
            'allies_name': '---',
            'enemies_name': '---',
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0
        }
        self._isHotkeyPressed = False
        self._activeKeys = {}

    def destroy(self):
        print_debug("[EloPanel] Destroying...")

        self._unregisterKeyHandlers()
        self._savePositionIfChanged()

        if self._hasGuiFlash and COMPONENT_EVENT:
            try:
                COMPONENT_EVENT.UPDATED -= self._onComponentUpdated
            except Exception:
                pass

        self._deleteAllComponents()

        if self._clanStateManager:
            try:
                self._clanStateManager.set_view(None)
            except Exception:
                pass
            self._clanStateManager = None

        print_debug("[EloPanel] Destroyed")
