# -*- coding: utf-8 -*-
import json

import BigWorld
import Keys
from gui import InputHandler

try:
    from gui import g_guiResetters
except ImportError:
    g_guiResetters = None

from ..battle_state_events import g_battleStateEvents
from ..settings import g_config
from ..settings.config_param import g_configParams, DisplayMode
from ..utils import logger

try:
    import GUI
    from openwg_gameface import ModDynAccessor, manager as gamefaceResMap, on_ready as gamefaceOnReady
    from frameworks.wulf import ViewFlags, ViewModel, ViewSettings, WindowFlags, WindowLayer, WindowStatus
    from gui.impl.gui_decorators import args2params
    from gui.impl.pub import ViewImpl, WindowImpl
    from helpers import dependency
    from skeletons.gui.impl import IGuiLoader
    _GF_OK = True
except Exception:
    GUI = None
    ModDynAccessor = gamefaceResMap = gamefaceOnReady = None
    ViewFlags = ViewModel = ViewSettings = WindowFlags = WindowLayer = WindowStatus = None
    ViewImpl = WindowImpl = args2params = None
    dependency = IGuiLoader = None
    _GF_OK = False

LAYOUT_KEY = 'mods/under_pressure/CalculationEloBattle/layoutID'
VIEW_NAME = 'CalculationEloBattle'
BASE_WIDTH = 140
PAD_TOP = 5
PAD_BOTTOM = 5
ROW_GAP_NAMES = 23
ROW_GAP_RATING = 26
ROW_GAP_SMALL = 18
BOUNDARY_GAP = 5
DRAG_THRESHOLD = 3
BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080
FIXED_COLORS = {
    'alliesNamesColor': '4F8627',
    'enemiesNamesColor': '9A0101',
    'alliesRatingColor': '4F8627',
    'enemiesRatingColor': '9A0101',
    'eloGainColor': '00FF00',
    'eloLossColor': 'FF0000'
}


def _registerGamefaceComponents():
    logger.debug('[EloPanel] Gameface components use dynamic res_map registration')


def _unregisterGamefaceComponents():
     logger.debug('[EloPanel] Gameface res_map unregistration')


def _cancelCallbackSafe(cbid):
    try:
        if cbid is not None:
            BigWorld.cancelCallback(cbid)
    except (AttributeError, ValueError):
        pass



def _screenResolution():
    try:
        if GUI is not None:
            width, height = GUI.screenResolution()
            if width > 0 and height > 0:
                return (int(width), int(height))
    except Exception:
        pass
    try:
        width, height = BigWorld.screenWidth(), BigWorld.screenHeight()
        if width > 0 and height > 0:
            return (int(width), int(height))
    except Exception:
        pass
    return (BASE_SCREEN_WIDTH, BASE_SCREEN_HEIGHT)


def _cursorPixels(cursor):
    normX, normY = cursor.position
    screenWidth, screenHeight = _screenResolution()
    return (int((normX + 1.0) * 0.5 * screenWidth), int((1.0 - normY) * 0.5 * screenHeight))


def _panelSize(scaleFactor):
    scale = scaleFactor if scaleFactor and scaleFactor > 0 else 1.0
    height = int(PAD_TOP * scale)
    if g_configParams.showTeamNames.value:
        height += int(ROW_GAP_NAMES * scale)
    height += int(ROW_GAP_RATING * scale)
    if g_configParams.showEloChanges.value:
        height += int(ROW_GAP_SMALL * scale)
    if g_configParams.showWinrateAndBattles.value:
        height += int(ROW_GAP_SMALL * scale)
    height += int(PAD_BOTTOM * scale)
    return (max(1, int(BASE_WIDTH * scale)), max(1, height))


if _GF_OK:
    _GF_LAYOUT = ModDynAccessor(LAYOUT_KEY)

    class _EloPanelModel(ViewModel):
        def __init__(self, payload):
            self._payload = payload
            super(_EloPanelModel, self).__init__(properties=1, commands=3)

        def _initialize(self):
            super(_EloPanelModel, self)._initialize()
            self._addStringProperty('payload', self._payload)
            self.onReady = self._addCommand('onReady')
            self.onDebug = self._addCommand('onDebug')
            self.onCmd = self._addCommand('onCmd')

        def setPayload(self, value):
            self._setString(0, value)

    class _EloPanelViewImpl(ViewImpl):
        def __init__(self, owner):
            self._owner = owner
            model = _EloPanelModel(owner.buildPayload())
            owner._setModel(model, publish=False)
            settings = ViewSettings(layoutID=_GF_LAYOUT(), flags=ViewFlags.VIEW, model=model)
            super(_EloPanelViewImpl, self).__init__(settings)

        def _getEvents(self):
            model = self.getViewModel()
            return (
                (model.onReady, self._owner._onReady),
                (model.onDebug, self._onDebug),
                (model.onCmd, self._onCmd),
            )

        @args2params(str)
        def _onDebug(self, message):
            logger.debug('[EloPanel] JS: %s', message)

        @args2params(str, str)
        def _onCmd(self, name, value):
            try:
                self._owner._handleCommand(name, value)
            except Exception:
                logger.exception('[EloPanel] command %s failed', name)

        def _finalize(self):
            self._owner._setModel(None)
            super(_EloPanelViewImpl, self)._finalize()
            self._owner._onViewFinalized()

    class _EloPanelWindow(WindowImpl):
        def __init__(self, content, parent):
            super(_EloPanelWindow, self).__init__(WindowFlags.WINDOW, content=content, layer=WindowLayer.OVERLAY, name=VIEW_NAME, parent=parent)


class EloPanel(object):
    def __init__(self):
        self._window = None
        self._model = None
        self._nativeReady = False
        self._token = 0
        self._destroyed = False
        self._isInitialized = False
        self._isVisible = False
        self._isHotkeyPressed = False
        self._activeKeys = {}
        self._clanStateManager = None
        self._currentDisplayMode = None
        self._currentState = self._defaultState()
        self._offset = list(g_config.configFile.panelOffset)
        self._position = [0, 0]
        self._positionChanged = False
        self._lastSavedOffset = tuple(self._offset)
        self._scaleFactor = 1.0
        self._size = _panelSize(self._scaleFactor)
        self._viewSizeReported = False
        self._guiResetterBound = False
        self._resizeCallbackID = None
        self._dragCallbackID = None
        self._dragging = False
        self._mouseWasDown = False
        self._dragStartCursor = None
        self._dragStartPosition = None

    @staticmethod
    def _defaultState():
        return {
            'allies_name': ' ', 'enemies_name': ' ',
            'allies_rating': 0, 'enemies_rating': 0,
            'elo_plus': 0, 'elo_minus': 0,
            'wins_percent': 0, 'battles_count': 0
        }

    def setClanStateManager(self, manager):
        self._clanStateManager = manager
        if manager:
            manager.set_view(self)

    def onBattleStart(self):
        if self._isInitialized:
            return
        self._destroyed = False
        self._nativeReady = False
        self._calculateScaleFactor()
        self._syncPositionFromOffset()
        displayMode = g_configParams.displayMode.value
        self._currentDisplayMode = displayMode
        self._isHotkeyPressed = (displayMode == DisplayMode.ALWAYS)
        self._isVisible = self._isHotkeyPressed and g_battleStateEvents.visible
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
        self._ensureWindow()
        self._startDragTicker()
        self._bindGuiResetter()

    def _onBattleClosed(self):
        self.onBattleEnd()

    def onBattleEnd(self):
        if not self._isInitialized:
            return
        self._isInitialized = False
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
        self._stopDragTicker()
        self._unbindGuiResetter()
        self._savePositionIfChanged()
        self._dropWindow()
        self._resetState()
        self._currentDisplayMode = None
        logger.debug('[EloPanel] Battle ended')

    def updateFromState(self, state):
        if state:
            self._currentState.update(state)
            if self._isInitialized:
                self.publish()

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
        self._stopDragTicker()
        self._unbindGuiResetter()
        self._savePositionIfChanged()
        self._destroyed = True
        self._dropWindow()
        self._isInitialized = False
        if self._clanStateManager:
            try:
                self._clanStateManager.set_view(None)
            except Exception:
                pass
            self._clanStateManager = None

    def buildPayload(self):
        self._syncSize()
        return json.dumps({
            'visible': bool(self._isVisible),
            'scale': self._scaleFactor,
            'size': {'w': self._size[0], 'h': self._size[1]},
            'config': self._buildConfigPayload(),
            'state': self._currentState
        }, ensure_ascii=False)

    def _buildConfigPayload(self):
        return {
            'showTeamNames': bool(g_configParams.showTeamNames.value),
            'showEloChanges': bool(g_configParams.showEloChanges.value),
            'showWinrateAndBattles': bool(g_configParams.showWinrateAndBattles.value),
            'alliesNamesColor': FIXED_COLORS['alliesNamesColor'],
            'enemiesNamesColor': FIXED_COLORS['enemiesNamesColor'],
            'alliesRatingColor': FIXED_COLORS['alliesRatingColor'],
            'enemiesRatingColor': FIXED_COLORS['enemiesRatingColor'],
            'eloGainColor': FIXED_COLORS['eloGainColor'],
            'eloLossColor': FIXED_COLORS['eloLossColor']
        }

    def _setModel(self, model, publish=True):
        self._model = model
        if publish:
            self.publish()

    def publish(self):
        if self._model is None:
            return
        payload = self.buildPayload()
        try:
            with self._model.transaction() as model:
                model.setPayload(payload)
        except Exception:
            pass
        self._move()

    def _onReady(self, *args):
        self._nativeReady = True
        self.publish()
        self._move()

    def _onViewFinalized(self):
        self._window = None
        self._model = None
        self._nativeReady = False
        self._token += 1
        if self._isInitialized and not self._destroyed:
            BigWorld.callback(0.1, self._ensureWindow)

    def _ensureWindow(self):
        if self._destroyed or self._window is not None:
            return
        if not _GF_OK or gamefaceResMap is None:
            logger.error('[EloPanel] openwg_gameface is required for Gameface panel')
            return
        self._token += 1
        token = self._token
        if gamefaceResMap.isResMapValidated:
            self._loadWindow(token)
        else:
            gamefaceOnReady(lambda: self._loadWindow(token))

    def _loadWindow(self, token, retry=0):
        if token != self._token or self._destroyed or not self._isInitialized:
            return
        try:
            parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        except Exception:
            parent = None
        if parent is None or parent.proxy is None or parent.windowStatus != WindowStatus.LOADED:
            if retry < 100:
                BigWorld.callback(0.1, lambda: self._loadWindow(token, retry + 1))
            return
        try:
            self._window = _EloPanelWindow(_EloPanelViewImpl(self), parent)
            self._window.load()
        except Exception:
            logger.exception('[EloPanel] Failed to load Gameface window')
            self._window = None

    def _dropWindow(self):
        self._token += 1
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
        self._model = None
        self._nativeReady = False

    def _move(self):
        if self._window is None or not self._nativeReady:
            return
        self._syncSize()
        self._clampPosition()
        scaleX, scaleY = self._windowScale()
        try:
            self._window.move(int(round(self._position[0] / scaleX)), int(round(self._position[1] / scaleY)))
        except Exception:
            pass

    def _windowScale(self):
        if self._window is None:
            return (1.0, 1.0)
        try:
            nativeW, nativeH = self._window.size[:2]
            nativeW = float(nativeW)
            nativeH = float(nativeH)
        except Exception:
            return (1.0, 1.0)
        viewW, viewH = self._size
        if nativeW <= 10 or nativeH <= 10 or viewW <= 10 or viewH <= 10:
            return (1.0, 1.0)
        scaleW = float(viewW) / nativeW
        scaleH = float(viewH) / nativeH
        if abs(scaleW - scaleH) > 0.1 or not 0.4 <= scaleW <= 4.0:
            return (1.0, 1.0)
        return (scaleW, scaleH)

    def _syncSize(self):
        if self._viewSizeReported:
            return False
        size = _panelSize(self._scaleFactor)
        if size != self._size:
            self._size = size
            return True
        return False

    def _anchor(self):
        screenWidth, _ = _screenResolution()
        self._syncSize()
        return (int(screenWidth * 0.5 - self._size[0] * 0.5), BOUNDARY_GAP)

    def _syncPositionFromOffset(self):
        anchorX, anchorY = self._anchor()
        self._position[0] = int(anchorX + self._offset[0])
        self._position[1] = int(anchorY + self._offset[1])
        self._clampPosition()

    def _syncOffsetFromPosition(self):
        anchorX, anchorY = self._anchor()
        self._offset = [int(self._position[0] - anchorX), int(self._position[1] - anchorY)]

    def _clampPosition(self):
        screenWidth, screenHeight = _screenResolution()
        width, height = self._size
        maxX = max(BOUNDARY_GAP, screenWidth - width - BOUNDARY_GAP)
        maxY = max(BOUNDARY_GAP, screenHeight - height - BOUNDARY_GAP)
        self._position[0] = max(BOUNDARY_GAP, min(int(self._position[0]), maxX))
        self._position[1] = max(BOUNDARY_GAP, min(int(self._position[1]), maxY))

    def _setPosition(self, xPos, yPos):
        oldPosition = tuple(self._position)
        self._position[0] = int(round(xPos))
        self._position[1] = int(round(yPos))
        self._clampPosition()
        if tuple(self._position) != oldPosition:
            self._positionChanged = True
            self._move()

    def _handleCommand(self, name, value):
        if name == 'onSize':
            try:
                parts = str(value).split('x')
                width = max(1, int(float(parts[0])))
                height = max(1, int(float(parts[1])))
            except (ValueError, IndexError):
                return
            self._viewSizeReported = True
            if (width, height) != tuple(self._size):
                self._size = (width, height)
                self._syncPositionFromOffset()
                self._move()

    def _bindGuiResetter(self):
        if self._guiResetterBound or g_guiResetters is None:
            return
        try:
            g_guiResetters.add(self._onScreenResize)
            self._guiResetterBound = True
        except Exception:
            pass

    def _unbindGuiResetter(self):
        if not self._guiResetterBound:
            return
        try:
            g_guiResetters.discard(self._onScreenResize)
        except Exception:
            pass
        self._guiResetterBound = False
        _cancelCallbackSafe(self._resizeCallbackID)
        self._resizeCallbackID = None

    def _onScreenResize(self, *args):
        if self._destroyed or self._window is None:
            return
        self._syncPositionFromOffset()
        self._move()
        _cancelCallbackSafe(self._resizeCallbackID)
        self._resizeCallbackID = BigWorld.callback(0.2, self._resizeResync)

    def _resizeResync(self):
        self._resizeCallbackID = None
        if self._destroyed or self._window is None:
            return
        self._syncPositionFromOffset()
        self._move()

    def _startDragTicker(self):
        if self._dragCallbackID is None:
            self._dragCallbackID = BigWorld.callback(0.0, self._updateDragState)

    def _stopDragTicker(self):
        _cancelCallbackSafe(self._dragCallbackID)
        self._dragCallbackID = None
        self._dragging = False
        self._mouseWasDown = False
        self._dragStartCursor = None
        self._dragStartPosition = None

    def _updateDragState(self):
        self._dragCallbackID = None
        if self._isInitialized and self._window is not None:
            self._handleMouseDrag()
            self._dragCallbackID = BigWorld.callback(0.0, self._updateDragState)

    def _handleMouseDrag(self):
        if GUI is None:
            return
        cursor = GUI.mcursor()
        mouseDown = BigWorld.isKeyDown(Keys.KEY_LEFTMOUSE)
        if not cursor.visible or not cursor.inWindow or not cursor.inFocus:
            if not mouseDown:
                if self._dragging:
                    self._finishDrag()
                self._mouseWasDown = False
            return
        cursorPos = _cursorPixels(cursor)
        if mouseDown and not self._mouseWasDown and self._isCursorOver(cursorPos):
            self._dragging = True
            self._dragStartCursor = cursorPos
            self._dragStartPosition = tuple(self._position)
        elif not mouseDown:
            if self._dragging:
                self._finishDrag()
            self._dragging = False
        if self._dragging and self._dragStartCursor is not None and self._dragStartPosition is not None:
            dx = cursorPos[0] - self._dragStartCursor[0]
            dy = cursorPos[1] - self._dragStartCursor[1]
            if dx * dx + dy * dy >= DRAG_THRESHOLD * DRAG_THRESHOLD:
                self._setPosition(self._dragStartPosition[0] + dx, self._dragStartPosition[1] + dy)
        self._mouseWasDown = mouseDown

    def _finishDrag(self):
        self._dragging = False
        self._syncOffsetFromPosition()
        self._savePositionIfChanged()

    def _isCursorOver(self, cursorPos):
        if not self._isVisible:
            return False
        left, top = self._position[0], self._position[1]
        width, height = self._size
        return left <= cursorPos[0] <= left + width and top <= cursorPos[1] <= top + height

    def _onConfigChanged(self):
        logger.debug('[EloPanel] Config changed, refreshing Gameface panel')
        newDisplayMode = g_configParams.displayMode.value
        if self._currentDisplayMode != newDisplayMode:
            oldDisplayMode = self._currentDisplayMode
            self._currentDisplayMode = newDisplayMode
            if oldDisplayMode == DisplayMode.ON_HOTKEY_PRESSED:
                self._unregisterKeyHandlers()
            self._activeKeys = {}
            if newDisplayMode == DisplayMode.ALWAYS:
                self._isHotkeyPressed = True
                self._updateVisibility(g_battleStateEvents.visible)
            elif newDisplayMode == DisplayMode.ON_HOTKEY_PRESSED:
                self._isHotkeyPressed = False
                self._registerKeyHandlers()
                self._updateVisibility(False)
        oldSize = self._size
        self._syncSize()
        if self._size != oldSize:
            self._syncPositionFromOffset()
        self.publish()

    def _onGUIVisibilityChanged(self, isVisible):
        if self._isInitialized and self._isHotkeyPressed:
            self._updateVisibility(isVisible)

    def _onInterfaceScaleChanged(self, scale):
        if self._isInitialized:
            self._calculateScaleFactor()
            self._syncPositionFromOffset()
            self.publish()

    def _calculateScaleFactor(self):
        try:
            interfaceScale = g_battleStateEvents.interfaceScale
            self._scaleFactor = interfaceScale if interfaceScale and interfaceScale > 0 else 1.0
        except Exception as e:
            logger.error('[EloPanel] Error calculating scale factor: %s', e)
            self._scaleFactor = 1.0
        self._syncSize()

    def _updateVisibility(self, isVisible):
        value = bool(isVisible)
        if self._isVisible != value:
            self._isVisible = value
            self.publish()

    def _savePositionIfChanged(self):
        if not self._positionChanged:
            return
        self._syncOffsetFromPosition()
        current = tuple(self._offset)
        if current != self._lastSavedOffset:
            g_config.configFile.panelOffset = list(self._offset)
            g_config.configFile.save_config()
            self._lastSavedOffset = current
            logger.debug('[EloPanel] Position saved: offset=(%s, %s)', self._offset[0], self._offset[1])
        self._positionChanged = False

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
        if all(self._activeKeys.get(key, False) for key in hotkeys) and not self._isHotkeyPressed:
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
        if not any(self._activeKeys.get(key, False) for key in hotkeys) and self._isHotkeyPressed:
            self._isHotkeyPressed = False
            self._updateVisibility(False)

    def _resetState(self):
        self._currentState = self._defaultState()
        self._isHotkeyPressed = False
        self._isVisible = False
        self._activeKeys = {}
