# -*- coding: utf-8 -*-
import json
import sys
from ..utils import logger

import ResMgr
from helpers import getClientLanguage

IS_PYTHON2 = sys.version_info[0] == 2


class TranslationError(Exception):
    pass


class TranslationManager(object):

    def __init__(self):
        self._defaultTranslationsMap = {}
        self._translationsMap = {}
        self._currentLanguage = None
        self._translationCache = {}
        self._translationsLoaded = False
        self.fallbackLanguage = "en"
        self.translationPathTemplate = "mods/under_pressure.CalculationElo/{}.json"

    def _safeJsonLoad(self, content, language):
        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            return json.loads(content)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            logger.error("[TranslationManager] Failed to parse JSON for language %s: %s", language, e)
            return None

    def _loadLanguageFile(self, language):
        try:
            translationPath = self.translationPathTemplate.format(language)
            translationsRes = ResMgr.openSection(translationPath)

            if translationsRes is None:
                logger.debug("[TranslationManager] Translation file not found for: %s", language)
                return None

            content = translationsRes.asBinary
            if not content:
                logger.debug("[TranslationManager] Empty translation file for: %s", language)
                return None

            return self._safeJsonLoad(content, language)

        except Exception as e:
            logger.error("[TranslationManager] Error loading translation file for %s: %s", language, e)
            return None

    def _validateTranslations(self, translations, language):
        if not isinstance(translations, dict):
            logger.error("[TranslationManager] Invalid format for %s: expected dict, got %s",
                        language, type(translations).__name__)
            return False
        return True

    def loadTranslations(self, forceReload=False):
        if self._translationsLoaded and not forceReload:
            return True

        try:
            defaultTranslations = self._loadLanguageFile(self.fallbackLanguage)

            if defaultTranslations is None:
                self._defaultTranslationsMap = self._getHardcodedDefaults()
                self._translationsMap = self._defaultTranslationsMap.copy()
                self._translationsLoaded = True
                return True

            if not self._validateTranslations(defaultTranslations, self.fallbackLanguage):
                return False

            self._defaultTranslationsMap = defaultTranslations

            try:
                clientLanguage = getClientLanguage()
            except Exception:
                clientLanguage = self.fallbackLanguage

            self._currentLanguage = clientLanguage

            if clientLanguage != self.fallbackLanguage:
                clientTranslations = self._loadLanguageFile(clientLanguage)

                if clientTranslations is not None and self._validateTranslations(clientTranslations, clientLanguage):
                    self._translationsMap = clientTranslations
                else:
                    self._translationsMap = defaultTranslations.copy()
            else:
                self._translationsMap = defaultTranslations.copy()

            self._translationCache.clear()
            self._translationsLoaded = True
            return True

        except Exception as e:
            logger.error("[TranslationManager] Critical error during translation loading: %s", e)
            self._defaultTranslationsMap = self._getHardcodedDefaults()
            self._translationsMap = self._defaultTranslationsMap.copy()
            self._translationsLoaded = True
            return True

    def _getHardcodedDefaults(self):
        return {
            "modname": "ELO Calculator",
            "checked": "enabled",
            "unchecked": "disabled",
            "defaultValue": "default",
            "displayMode.always": "Always",
            "displayMode.onHotkeyPressed": "When hotkey is pressed",
            "eloHotKey.header": "Hotkey",
            "eloHotKey.body": "Set the hotkey to display the mod",
            "displayMode.header": "Display mode",
            "displayMode.body": "Select when to display the widget",
            "panelPositionX.header": "Panel X position",
            "panelPositionX.body": "Sets the horizontal position of the panel",
            "panelPositionY.header": "Panel Y position",
            "panelPositionY.body": "Sets the vertical position of the panel",
            "showTitleVisible.header": "Show title",
            "showTitleVisible.body": "Displays or hides the mod title",
            "showTeamNames.header": "Show team names",
            "showTeamNames.body": "Displays or hides team names",
            "showEloChanges.header": "Show ELO changes",
            "showEloChanges.body": "Displays or hides ELO changes after battle",
            "showWinrateAndBattles.header": "Show winrate and battles",
            "showWinrateAndBattles.body": "Displays or hides winrate and battles count",
            "headerColor.header": "Header color",
            "headerColor.body": "Sets the color for the header",
            "alliesNamesColor.header": "Allies names color",
            "alliesNamesColor.body": "Sets the color for allies clan names",
            "enemiesNamesColor.header": "Enemies names color",
            "enemiesNamesColor.body": "Sets the color for enemies clan names",
            "alliesRatingColor.header": "Allies rating color",
            "alliesRatingColor.body": "Sets the color for allies ratings",
            "enemiesRatingColor.header": "Enemies rating color",
            "enemiesRatingColor.body": "Sets the color for enemies ratings",
            "eloGainColor.header": "ELO gain color",
            "eloGainColor.body": "Sets the color for ELO gain",
            "eloLossColor.header": "ELO loss color",
            "eloLossColor.body": "Sets the color for ELO loss"
        }

    def getCurrentLanguage(self):
        return self._currentLanguage or self.fallbackLanguage

    def initialize(self):
        try:
            self.loadTranslations()
        except Exception as e:
            logger.error("[TranslationManager] Critical error initializing translations: %s", e)


g_translationManager = TranslationManager()
g_translationManager.initialize()


class TranslationBase(object):

    def __init__(self, tokenName, manager=None):
        self._tokenName = tokenName
        self._cachedValue = None
        self._manager = manager or g_translationManager

    def __get__(self, instance, owner=None):
        if self._cachedValue is None:
            self._cachedValue = self._generateTranslation()
        return self._cachedValue

    def _generateTranslation(self):
        raise NotImplementedError

    def invalidateCache(self):
        self._cachedValue = None


class TranslationElement(TranslationBase):

    def _generateTranslation(self):
        if not self._manager._translationsLoaded:
            self._manager.loadTranslations()

        cached = self._manager._translationCache.get(self._tokenName)
        if cached is not None:
            return cached

        translation = None
        if self._tokenName in self._manager._translationsMap:
            translation = self._manager._translationsMap[self._tokenName]
        elif self._tokenName in self._manager._defaultTranslationsMap:
            translation = self._manager._defaultTranslationsMap[self._tokenName]
        else:
            translation = self._tokenName.replace('.', ' ').replace('_', ' ').title()

        self._manager._translationCache[self._tokenName] = translation
        return translation


class Translator(object):
    MOD_NAME = TranslationElement("modname")
    CHECKED = TranslationElement("checked")
    UNCHECKED = TranslationElement("unchecked")
    DEFAULT_VALUE = TranslationElement("defaultValue")
    ALWAYS = TranslationElement("displayMode.always")
    ON_HOTKEY_PRESSED = TranslationElement("displayMode.onHotkeyPressed")
    ELO_HOTKEY_HEADER = TranslationElement("eloHotKey.header")
    ELO_HOTKEY_BODY = TranslationElement("eloHotKey.body")
    DISPLAY_MODE_HEADER = TranslationElement("displayMode.header")
    DISPLAY_MODE_BODY = TranslationElement("displayMode.body")
    PANEL_POSITION_X_HEADER = TranslationElement("panelPositionX.header")
    PANEL_POSITION_X_BODY = TranslationElement("panelPositionX.body")
    PANEL_POSITION_Y_HEADER = TranslationElement("panelPositionY.header")
    PANEL_POSITION_Y_BODY = TranslationElement("panelPositionY.body")
    SHOW_TITLE_VISIBLE_HEADER = TranslationElement("showTitleVisible.header")
    SHOW_TITLE_VISIBLE_BODY = TranslationElement("showTitleVisible.body")
    SHOW_TEAM_NAMES_HEADER = TranslationElement("showTeamNames.header")
    SHOW_TEAM_NAMES_BODY = TranslationElement("showTeamNames.body")
    SHOW_ELO_CHANGES_HEADER = TranslationElement("showEloChanges.header")
    SHOW_ELO_CHANGES_BODY = TranslationElement("showEloChanges.body")
    SHOW_WINRATE_AND_BATTLES_HEADER = TranslationElement("showWinrateAndBattles.header")
    SHOW_WINRATE_AND_BATTLES_BODY = TranslationElement("showWinrateAndBattles.body")
    HEADER_COLOR_HEADER = TranslationElement("headerColor.header")
    HEADER_COLOR_BODY = TranslationElement("headerColor.body")
    ALLIES_NAMES_COLOR_HEADER = TranslationElement("alliesNamesColor.header")
    ALLIES_NAMES_COLOR_BODY = TranslationElement("alliesNamesColor.body")
    ENEMIES_NAMES_COLOR_HEADER = TranslationElement("enemiesNamesColor.header")
    ENEMIES_NAMES_COLOR_BODY = TranslationElement("enemiesNamesColor.body")
    ALLIES_RATING_COLOR_HEADER = TranslationElement("alliesRatingColor.header")
    ALLIES_RATING_COLOR_BODY = TranslationElement("alliesRatingColor.body")
    ENEMIES_RATING_COLOR_HEADER = TranslationElement("enemiesRatingColor.header")
    ENEMIES_RATING_COLOR_BODY = TranslationElement("enemiesRatingColor.body")
    ELO_GAIN_COLOR_HEADER = TranslationElement("eloGainColor.header")
    ELO_GAIN_COLOR_BODY = TranslationElement("eloGainColor.body")
    ELO_LOSS_COLOR_HEADER = TranslationElement("eloLossColor.header")
    ELO_LOSS_COLOR_BODY = TranslationElement("eloLossColor.body")


def getTranslation(key):
    if not g_translationManager._translationsLoaded:
        g_translationManager.loadTranslations()

    if key in g_translationManager._translationsMap:
        return g_translationManager._translationsMap[key]
    elif key in g_translationManager._defaultTranslationsMap:
        return g_translationManager._defaultTranslationsMap[key]
    return key.replace('.', ' ').replace('_', ' ').title()
