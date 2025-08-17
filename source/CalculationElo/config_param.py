# -*- coding: utf-8 -*-
import Keys
from .config_param_types import BooleanParam, OptionsParam, ColorParam, ListParam, Option, PARAM_REGISTRY

class DisplayMode(object):
    ALWAYS = 'always'
    ON_HOTKEY_PRESSED = 'on-hotkey-pressed'

class HotKeyParam(object):
    def __init__(self, path, defaultValue=None):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue if defaultValue is not None else []
        self.defaultValue = self.value
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def defaultMsaValue(self):
        return self.value

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        if isinstance(value, list):
            self.value = value
        elif value is None:
            self.value = []
        else:
            self.value = [value]

class ConfigParams(object):
    def __init__(self):
        self.enabled = BooleanParam(['enabled'], defaultValue=True)
        self.displayMode = OptionsParam(
            ['display-mode'],
            [
                Option(DisplayMode.ALWAYS, 0, "Always"),
                Option(DisplayMode.ON_HOTKEY_PRESSED, 1, "On HotKey Pressed")
            ],
            defaultValue=DisplayMode.ALWAYS
        )
        self.eloHotKey = HotKeyParam(['elo-hotkey'], defaultValue=[Keys.KEY_LALT])

        self.panelPosition = ListParam(['panel-position'], defaultValue=[560, 50])
        
        self.headerColor = ColorParam(['header-color'], defaultValue=[255, 255, 255])
        self.alliesNamesColor = ColorParam(['allies-names-color'], defaultValue=[79, 134, 39])
        self.enemiesNamesColor = ColorParam(['enemies-names-color'], defaultValue=[154, 1, 1])
        self.alliesRatingColor = ColorParam(['allies-rating-color'], defaultValue=[79, 134, 39])
        self.enemiesRatingColor = ColorParam(['enemies-rating-color'], defaultValue=[154, 1, 1])
        self.eloGainColor = ColorParam(['elo-gain-color'], defaultValue=[0, 255, 0])
        self.eloLossColor = ColorParam(['elo-loss-color'], defaultValue=[255, 0, 0])
        self.winrateColor = ColorParam(['winrate-color'], defaultValue=[255, 255, 0])
        self.battlesColor = ColorParam(['battles-color'], defaultValue=[255, 255, 255])
        self.avgWN8Color = ColorParam(['avg-wn8-color'], defaultValue=[255, 255, 255])

        self.showTitleVisible = BooleanParam(['show-title-visible'], defaultValue=False)
        self.showTeamNames = BooleanParam(['show-team-names'], defaultValue=True)
        self.showEloChanges = BooleanParam(['show-elo-changes'], defaultValue=True)
        self.showWinrateAndBattles = BooleanParam(['show-winrate-and-battles'], defaultValue=True)
        self.showAvgTeamWn8 = BooleanParam(['show-avg-team-wn8'], defaultValue=False)
        self.recordAvgTeamWn8 = BooleanParam(['record-avg-team-wn8'], defaultValue=False)

        self.textShadowEnabled = BooleanParam(['text-shadow-enabled'], defaultValue=True)
        self.textShadowColor = ColorParam(['text-shadow-color'], defaultValue=[0, 0, 0])
        self.textShadowDistance = ListParam(['text-shadow-distance'], defaultValue=[1])
        self.textShadowAlpha = ListParam(['text-shadow-alpha'], defaultValue=[0.5])
        self.textShadowBlur = ListParam(['text-shadow-blur'], defaultValue=[2])

    @staticmethod
    def items():
        return PARAM_REGISTRY

g_configParams = ConfigParams()