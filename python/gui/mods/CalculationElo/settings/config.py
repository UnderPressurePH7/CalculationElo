# -*- coding: utf-8 -*-
import BigWorld
from .config_param_types import LabelParameter
from .config_file import ConfigFile
from .config_param import ConfigParams, g_configParams
from .config_template import Template
from .translations import Translator
from ..utils import logger

try:
    from gui.modsSettingsApi import g_modsSettingsApi   
except ImportError:
    logger.error('[Config] Failed to import g_modsSettingsApi')
    g_modsSettingsApi = None

MOD_LINKAGE = 'me.under-pressure.calculationelo'


class Config(object):
    
    def __init__(self):
        logger.debug('[Config] Initializing configuration')
        self.configParams = g_configParams
        self.configTemplate = Template(self.configParams)
        self.configFile = ConfigFile(self.configParams)
        self._loadedSuccessfully = False
        
        self._loadConfigFileToParams()
        
        if g_modsSettingsApi:
            self._registerMod()

    def _registerMod(self):
        if not g_modsSettingsApi:
            logger.debug('[Config] ModsSettingsAPI not available')
            return
            
        try:
            self.configTemplate.setModDisplayName(Translator.MOD_NAME)
            
            self.configTemplate.addParameterToColumn1(
                'eloHotKey', 
                header=Translator.ELO_HOTKEY_HEADER,
                body=Translator.ELO_HOTKEY_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'displayMode', 
                header=Translator.DISPLAY_MODE_HEADER,
                body=Translator.DISPLAY_MODE_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'panelPositionX', 
                header=Translator.PANEL_POSITION_X_HEADER,
                body=Translator.PANEL_POSITION_X_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'panelPositionY', 
                header=Translator.PANEL_POSITION_Y_HEADER,
                body=Translator.PANEL_POSITION_Y_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'showTitleVisible',
                header=Translator.SHOW_TITLE_VISIBLE_HEADER,
                body=Translator.SHOW_TITLE_VISIBLE_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'showTeamNames',
                header=Translator.SHOW_TEAM_NAMES_HEADER,
                body=Translator.SHOW_TEAM_NAMES_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'showEloChanges',
                header=Translator.SHOW_ELO_CHANGES_HEADER,
                body=Translator.SHOW_ELO_CHANGES_BODY
            )
            self.configTemplate.addParameterToColumn1(
                'showWinrateAndBattles',
                header=Translator.SHOW_WINRATE_AND_BATTLES_HEADER,
                body=Translator.SHOW_WINRATE_AND_BATTLES_BODY
            )

            self.configTemplate.addParameterToColumn2(
                'headerColor',
                header=Translator.HEADER_COLOR_HEADER,
                body=Translator.HEADER_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'alliesNamesColor',
                header=Translator.ALLIES_NAMES_COLOR_HEADER,
                body=Translator.ALLIES_NAMES_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'enemiesNamesColor',
                header=Translator.ENEMIES_NAMES_COLOR_HEADER,
                body=Translator.ENEMIES_NAMES_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'alliesRatingColor',
                header=Translator.ALLIES_RATING_COLOR_HEADER,
                body=Translator.ALLIES_RATING_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'enemiesRatingColor',
                header=Translator.ENEMIES_RATING_COLOR_HEADER,
                body=Translator.ENEMIES_RATING_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'eloGainColor',
                header=Translator.ELO_GAIN_COLOR_HEADER,
                body=Translator.ELO_GAIN_COLOR_BODY
            )
            self.configTemplate.addParameterToColumn2(
                'eloLossColor',
                header=Translator.ELO_LOSS_COLOR_HEADER,
                body=Translator.ELO_LOSS_COLOR_BODY
            )

            template = self.configTemplate.generateTemplate()
            logger.debug('[Config] Template = %s', template)

            settings = g_modsSettingsApi.setModTemplate(
                MOD_LINKAGE, 
                template, 
                self._onSettingsChanged
            )
            
            if settings:
                self._applySettingsFromMsa(settings)
            
            logger.debug('[Config] Mod template registered successfully')
            
        except Exception as e:
            import traceback
            logger.error('[Config] Error registering mod template: %s', e)
            logger.error('[Config] Traceback: %s', traceback.format_exc())

    def _applySettingsFromMsa(self, settings):
        try:
            configItems = self.configParams.items()
            for paramName, value in settings.items():
                if paramName in configItems:
                    param = configItems[paramName]
                    try:
                        param.msaValue = value
                    except Exception as e:
                        logger.error('[Config] Error applying MSA setting %s = %s: %s',
                                     paramName, value, e)
            
            self.configFile.save_config()
            logger.debug('[Config] Applied settings from MSA')
            
        except Exception as e:
            logger.error('[Config] Error applying MSA settings: %s', e)

    def _onSettingsChanged(self, linkage, newSettings):
        if linkage != MOD_LINKAGE:
            return

        if not self._loadedSuccessfully:
            logger.error('[Config] Settings change cancelled - config not loaded properly')
            self._loadConfigFileToParams()
            if not self._loadedSuccessfully:
                return
            
        try:
            logger.debug('[Config] MSA settings changed: %s', newSettings)

            configItems = self.configParams.items()
            for tokenName, value in newSettings.items():
                if tokenName in configItems:
                    param = configItems[tokenName]
                    try:
                        param.msaValue = value
                    except Exception as e:
                        logger.error('[Config] Error setting parameter %s to %s: %s',
                                     tokenName, value, e)

            self.configFile.save_config()
            self._notifyConfigChanged()
            logger.debug('[Config] Settings updated successfully')
            
        except Exception as e:
            logger.error('[Config] Error updating settings from MSA: %s', e)

    def _notifyConfigChanged(self):
        pass

    def _loadConfigFileToParams(self):
        logger.debug('[Config] Starting config loading...')
        self._loadedSuccessfully = False

        try:
            success = self.configFile.load_config()
            if success:
                self._loadedSuccessfully = True
                logger.debug('[Config] Finished config loading.')
            else:
                logger.error('[Config] Config loading failed, using defaults')
            
            if not self.configFile.exists():
                logger.debug('[Config] Config file does not exist, creating it')
                self.configFile.save_config()
                
        except Exception as e:
            logger.error('[Config] Failed to load config: %s', e)
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                param.value = param.defaultValue

    def syncWithMsa(self):
        try:
            if g_modsSettingsApi:
                currentSettings = {}
                configItems = self.configParams.items()
                for paramName, param in configItems.items():
                    currentSettings[paramName] = param.msaValue
                
                g_modsSettingsApi.updateModSettings(MOD_LINKAGE, currentSettings)
                logger.debug('[Config] Synchronized with MSA')
        except Exception as e:
            logger.error('[Config] Error in MSA sync: %s', e)

    def backupConfig(self):
        return self.configFile.backup_config()

    def restoreConfig(self):
        if self.configFile.restore_config():
            self._loadConfigFileToParams()
            return True
        return False
