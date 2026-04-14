# -*- coding: utf-8 -*-
import Keys
from .config_param_types import (
    CheckboxParameter,
    ColorParameter,
    RadioButtonGroupParameter,
    OptionItem,
    HotkeyParameter
)
from .translations import Translator


class DisplayMode(object):
    ALWAYS = 'always'
    ON_HOTKEY_PRESSED = 'on-hotkey-pressed'


class ConfigParams(object):

    def __init__(self):
        self._items_cache = None

        self.enabled = CheckboxParameter(
            ['enabled'],
            defaultValue=True
        )

        self.eloHotKey = HotkeyParameter(
            ['elo-hotkey'],
            defaultValue=[Keys.KEY_LALT]
        )

        self.displayMode = RadioButtonGroupParameter(
            ['display-mode'],
            [
                OptionItem(DisplayMode.ALWAYS, 0, Translator.ALWAYS),
                OptionItem(DisplayMode.ON_HOTKEY_PRESSED, 1, Translator.ON_HOTKEY_PRESSED)
            ],
            defaultValue=DisplayMode.ALWAYS
        )

        self.headerColor = ColorParameter(
            ['header-color'],
            defaultValue=[255, 255, 255]
        )

        self.alliesNamesColor = ColorParameter(
            ['allies-names-color'],
            defaultValue=[79, 134, 39]
        )

        self.enemiesNamesColor = ColorParameter(
            ['enemies-names-color'],
            defaultValue=[154, 1, 1]
        )

        self.alliesRatingColor = ColorParameter(
            ['allies-rating-color'],
            defaultValue=[79, 134, 39]
        )

        self.enemiesRatingColor = ColorParameter(
            ['enemies-rating-color'],
            defaultValue=[154, 1, 1]
        )

        self.eloGainColor = ColorParameter(
            ['elo-gain-color'],
            defaultValue=[0, 255, 0]
        )

        self.eloLossColor = ColorParameter(
            ['elo-loss-color'],
            defaultValue=[255, 0, 0]
        )

        self.showTitleVisible = CheckboxParameter(
            ['show-title-visible'],
            defaultValue=False
        )

        self.showTeamNames = CheckboxParameter(
            ['show-team-names'],
            defaultValue=True
        )

        self.showEloChanges = CheckboxParameter(
            ['show-elo-changes'],
            defaultValue=True
        )

        self.showWinrateAndBattles = CheckboxParameter(
            ['show-winrate-and-battles'],
            defaultValue=True
        )

    def items(self):
        if self._items_cache is not None:
            return self._items_cache

        result = {}
        for attrName in dir(self):
            if attrName.startswith('_') or attrName == 'items':
                continue
            try:
                attr = getattr(self, attrName)
                if hasattr(attr, 'tokenName') and hasattr(attr, 'defaultValue'):
                    result[attr.tokenName] = attr
            except Exception:
                continue

        self._items_cache = result
        return self._items_cache


g_configParams = ConfigParams()
