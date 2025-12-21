# -*- coding: utf-8 -*-
import json
import threading
from ..utils import print_debug, print_error

import ResMgr
from helpers import getClientLanguage


class TranslationError(Exception):
    pass

class TranslationManager(object):

    def __init__(self):
        self._defaultTranslationsMap = {}
        self._translationsMap = {}
        self._currentLanguage = None
        self._translationCache = {}
        self._cacheLock = threading.Lock()
        self._translationsLoaded = False
        self.fallbackLanguage = "en"
        self.translationPathTemplate = "mods/under_pressure.CalculationElo/{}.json"

    def _safeJsonLoad(self, content, language):
        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            return json.loads(content)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            _("[TranslationManager] Failed to parse JSON for language {}: {}".format(language, e))
            return None

    def _loadLanguageFile(self, language):
        try:
            translationPath = self.translationPathTemplate.format(language)
            translationsRes = ResMgr.openSection(translationPath)

            if translationsRes is None:
                print_debug("[TranslationManager] Translation file not found for language: {}".format(language))
                return None

            content = translationsRes.asBinary
            if not content:
                _print_debug("[TranslationManager] Empty translation file for language: {}".format(language))
                return None

            return self._safeJsonLoad(content, language)

        except Exception as e:
            print_error("[TranslationManager] Error loading translation file for {}: {}".format(language, e))
            return None

    def _validateTranslations(self, translations, language):
        if not isinstance(translations, dict):
            print_error("[TranslationManager] Invalid translation format for {}: expected dict, got {}".format(
                language, type(translations).__name__))
            return False

        emptyKeys = [key for key, value in translations.items() if not value or not str(value).strip()]
        if emptyKeys:
            print_debug("[TranslationManager] Empty translation values in {} for keys: {}".format(language, emptyKeys))

        return True

    def loadTranslations(self, forceReload=False):
        if self._translationsLoaded and not forceReload:
            print_debug("[TranslationManager] Translations already loaded, skipping...")
            return True

        try:
            print_debug("[TranslationManager] Loading default translations ({})...".format(self.fallbackLanguage))
            defaultTranslations = self._loadLanguageFile(self.fallbackLanguage)

            if defaultTranslations is None:
                print_error("[TranslationManager] Failed to load default translations. Using hardcoded defaults.")
                self._defaultTranslationsMap = self._getHardcodedDefaults()
                self._translationsMap = self._defaultTranslationsMap.copy()
                self._translationsLoaded = True
                return True

            if not self._validateTranslations(defaultTranslations, self.fallbackLanguage):
                print_error("[TranslationManager] Invalid default translation format")
                return False

            self._defaultTranslationsMap = defaultTranslations

            try:
                clientLanguage = getClientLanguage()
            except Exception:
                clientLanguage = self.fallbackLanguage

            self._currentLanguage = clientLanguage
            print_debug("[TranslationManager] Detected client language: {}".format(clientLanguage))

            if clientLanguage != self.fallbackLanguage:
                clientTranslations = self._loadLanguageFile(clientLanguage)

                if clientTranslations is not None and self._validateTranslations(clientTranslations, clientLanguage):
                    print_debug("[TranslationManager] Loaded translations for language: {}".format(clientLanguage))
                    self._translationsMap = clientTranslations
                else:
                    print_debug("[TranslationManager] Failed to load {} translations, using {} as fallback".format(
                        clientLanguage, self.fallbackLanguage))
                    self._translationsMap = defaultTranslations.copy()
            else:
                self._translationsMap = defaultTranslations.copy()

            self._clearCache()
            self._translationsLoaded = True

            print_debug("[TranslationManager] Translation system initialized successfully")
            return True

        except Exception as e:
            print_error("[TranslationManager] Critical error during translation loading: {}".format(e))
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

    def _clearCache(self):
        with self._cacheLock:
            self._translationCache.clear()

    def getCurrentLanguage(self):
        return self._currentLanguage or self.fallbackLanguage

    def _getCachedTranslation(self, tokenName):
        with self._cacheLock:
            return self._translationCache.get(tokenName)

    def _cacheTranslation(self, tokenName, translation):
        with self._cacheLock:
            self._translationCache[tokenName] = translation

    def initialize(self):
        try:
            success = self.loadTranslations()
            if not success:
                print_error("[TranslationManager] Failed to initialize translation system")
        except Exception as e:
            print_error("[TranslationManager] Critical error initializing translations: {}".format(e))


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
        raise NotImplementedError("Subclasses must implement _generateTranslation")

    def invalidateCache(self):
        self._cachedValue = None


class TranslationElement(TranslationBase):

    def _generateTranslation(self):
        if not self._manager._translationsLoaded:
            print_debug("[TranslationElement] Translations not loaded, attempting to load...")
            self._manager.loadTranslations()

        cached = self._manager._getCachedTranslation(self._tokenName)
        if cached is not None:
            return cached

        translation = None
        if self._tokenName in self._manager._translationsMap:
            translation = self._manager._translationsMap[self._tokenName]
        elif self._tokenName in self._manager._defaultTranslationsMap:
            translation = self._manager._defaultTranslationsMap[self._tokenName]
        else:
            print_debug("[TranslationElement] Translation not found for token: {}".format(self._tokenName))
            translation = self._tokenName.replace('.', ' ').replace('_', ' ').title()

        self._manager._cacheTranslation(self._tokenName, translation)
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
    else:
        return key.replace('.', ' ').replace('_', ' ').title()
