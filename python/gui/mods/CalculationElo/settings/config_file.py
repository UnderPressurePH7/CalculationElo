# -*- coding: utf-8 -*-
import json
import os
from ..utils import logger, byteify

_DEFAULT_PANEL_OFFSET = [300, 50]


def _toOffsetList(value, default):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return [int(value[0]), int(value[1])]
        except (TypeError, ValueError):
            pass
    return list(default)


class ConfigFile(object):

    def __init__(self, configParams):
        self.configPath = os.path.join('mods', 'configs', 'under_pressure', 'calculationelo.json')
        self.configParams = configParams
        self._loadedConfigData = None
        self._save_rev = 0
        self.panelOffset = list(_DEFAULT_PANEL_OFFSET)

    def _ensureConfigExists(self):
        try:
            configDir = os.path.dirname(self.configPath)
            if not os.path.exists(configDir):
                os.makedirs(configDir)
                logger.debug('[ConfigFile] Created config directory: %s', configDir)

            if not os.path.exists(self.configPath):
                logger.debug('[ConfigFile] Config file does not exist, creating default')
                return self._createDefaultConfig()
            return True
        except Exception as e:
            logger.error('[ConfigFile] Error ensuring config exists: %s', e)
            return False

    def _createDefaultConfig(self):
        try:
            configData = {}
            configItems = self.configParams.items()
            
            for tokenName, param in configItems.items():
                configData[tokenName] = param.defaultValue
            configData['panel-offset'] = list(_DEFAULT_PANEL_OFFSET)

            with open(self.configPath, 'w') as f:
                json.dump(configData, f, indent=4, ensure_ascii=False)

            logger.debug('[ConfigFile] Created default config at: %s', self.configPath)
            return os.path.exists(self.configPath)
            
        except Exception as e:
            logger.error('[ConfigFile] Error creating default config: %s', e)
            return False

    def load_config(self):
        try:
            if not self._ensureConfigExists():
                logger.error('[ConfigFile] Failed to ensure config exists')
                self._applyDefaults()
                return False
                
            with open(self.configPath, 'r') as f:
                content = f.read().strip()
                
            if not content:
                logger.debug('[ConfigFile] Config file is empty, recreating')
                if not self._createDefaultConfig():
                    return False
                with open(self.configPath, 'r') as f:
                    content = f.read().strip()

            configData = byteify(json.loads(content))
            self._loadedConfigData = configData 
            logger.debug('[ConfigFile] Loaded config data: %s', configData)
            
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                if tokenName in configData:
                    try:
                        param.value = configData[tokenName]
                    except Exception as e:
                        logger.error('[ConfigFile] Error loading parameter %s: %s', tokenName, e)
                        param.value = param.defaultValue
                else:
                    param.value = param.defaultValue

            self.panelOffset = _toOffsetList(configData.get('panel-offset'), _DEFAULT_PANEL_OFFSET)

            logger.debug('[ConfigFile] Config loaded successfully')
            return True
                
        except ValueError as e:
            logger.error('[ConfigFile] Invalid JSON in config file: %s', e)
            self._loadedConfigData = None
            self._applyDefaults()
            return False
        except Exception as e:
            logger.error('[ConfigFile] Error loading config: %s', e)
            self._loadedConfigData = None
            self._applyDefaults()
            return False

    def _applyDefaults(self):
        configItems = self.configParams.items()
        for tokenName, param in configItems.items():
            param.value = param.defaultValue

    def save_config(self):
        try:
            configDir = os.path.dirname(self.configPath)
            if not os.path.exists(configDir):
                os.makedirs(configDir)
            
            configData = {}
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                configData[tokenName] = param.value
            configData['panel-offset'] = list(self.panelOffset)

            with open(self.configPath, 'w') as f:
                json.dump(configData, f, indent=4, ensure_ascii=False)

            self._loadedConfigData = configData
            logger.debug('[ConfigFile] Config saved to: %s', self.configPath)
            return True
            
        except Exception as e:
            logger.error('[ConfigFile] Error saving config: %s', e)
            return False

    def getLoadedData(self):
        return self._loadedConfigData

    def exists(self):
        return os.path.exists(self.configPath)

    def configExists(self):
        return self.exists()

    def getConfigPath(self):
        return self.configPath

    def backup_config(self, backupSuffix='.backup'):
        try:
            if self.configExists():
                backupPath = self.configPath + backupSuffix
                import shutil
                shutil.copy2(self.configPath, backupPath)
                logger.debug('[ConfigFile] Backup created: %s', backupPath)
                return True
        except Exception as e:
            logger.error('[ConfigFile] Error creating backup: %s', e)
        return False

    def restore_config(self, backupSuffix='.backup'):
        try:
            backupPath = self.configPath + backupSuffix
            if os.path.exists(backupPath):
                import shutil
                shutil.copy2(backupPath, self.configPath)
                logger.debug('[ConfigFile] Config restored from backup')
                return True
        except Exception as e:
            logger.error('[ConfigFile] Error restoring from backup: %s', e)
        return False
