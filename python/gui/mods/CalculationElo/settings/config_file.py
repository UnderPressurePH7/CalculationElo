# -*- coding: utf-8 -*-
import json
import os
from ..utils import print_error, print_debug


class ConfigFile(object):

    def __init__(self, configParams):
        self.configPath = os.path.join('mods', 'configs', 'under_pressure', 'calculationelo.json')
        self.configParams = configParams
        self._loadedConfigData = None

    def _ensureConfigExists(self):
        try:
            configDir = os.path.dirname(self.configPath)
            if not os.path.exists(configDir):
                os.makedirs(configDir)
                print_debug("[ConfigFile] Created config directory: {}".format(configDir))

            if not os.path.exists(self.configPath):
                print_debug("[ConfigFile] Config file doesn't exist, creating default")
                return self._createDefaultConfig()
            return True
        except Exception as e:
            print_error("[ConfigFile] Error ensuring config exists: {}".format(str(e)))
            return False

    def _createDefaultConfig(self):
        try:
            configData = {}
            configItems = self.configParams.items()
            
            print_debug("[ConfigFile] Creating config with {} parameters".format(len(configItems)))
            
            for tokenName, param in configItems.items():
                configData[tokenName] = param.defaultValue
                print_debug("[ConfigFile] Added default: {} = {}".format(tokenName, param.defaultValue))

            with open(self.configPath, 'w') as f:
                json.dump(configData, f, indent=4, ensure_ascii=False)
            
            print_debug("[ConfigFile] Created default config file at: {}".format(self.configPath))
            
            if os.path.exists(self.configPath):
                with open(self.configPath, 'r') as f:
                    content = f.read()
                print_debug("[ConfigFile] Verified file content: {}".format(content[:200]))
                return True
            else:
                print_error("[ConfigFile] File was not created despite no errors")
                return False
            
        except Exception as e:
            print_error("[ConfigFile] Error creating default config: {}".format(str(e)))
            return False

    def load_config(self):
        try:
            if not self._ensureConfigExists():
                print_error("[ConfigFile] Failed to ensure config exists")
                configItems = self.configParams.items()
                for tokenName, param in configItems.items():
                    param.value = param.defaultValue
                return False
            
            if not os.path.exists(self.configPath):
                print_error("[ConfigFile] Config file still doesn't exist after creation")
                return False
                
            with open(self.configPath, 'r') as f:
                content = f.read().strip()
                
            if not content:
                print_debug("[ConfigFile] Config file is empty, recreating")
                if self._createDefaultConfig():
                    with open(self.configPath, 'r') as f:
                        content = f.read().strip()
                else:
                    return False

            configData = json.loads(content)
            self._loadedConfigData = configData 
            print_debug("[ConfigFile] Loaded config data: {}".format(configData))
            
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                if tokenName in configData:
                    try:
                        param.value = configData[tokenName]
                        print_debug("[ConfigFile] Set {} = {}".format(tokenName, param.value))
                    except Exception as e:
                        print_error("[ConfigFile] Error loading parameter {}: {}".format(tokenName, str(e)))
                        param.value = param.defaultValue
                else:
                    param.value = param.defaultValue
                    print_debug("[ConfigFile] Using default for {}: {}".format(tokenName, param.defaultValue))

            print_debug("[ConfigFile] Config loaded successfully")
            return True
                
        except ValueError as e:
            print_error("[ConfigFile] Invalid JSON in config file: {}".format(str(e)))
            self._loadedConfigData = None
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                param.value = param.defaultValue
            return False
        except Exception as e:
            print_error("[ConfigFile] Error loading config: {}".format(str(e)))
            self._loadedConfigData = None
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                param.value = param.defaultValue
            return False

    def save_config(self):
        try:
            configDir = os.path.dirname(self.configPath)
            if not os.path.exists(configDir):
                os.makedirs(configDir)
                print_debug("[ConfigFile] Created directory for save: {}".format(configDir))
            
            configData = {}
            configItems = self.configParams.items()
            for tokenName, param in configItems.items():
                configData[tokenName] = param.value
                print_debug("[ConfigFile] Preparing to save: {} = {}".format(tokenName, param.value))

            with open(self.configPath, 'w') as f:
                json.dump(configData, f, indent=4, ensure_ascii=False)
            
            self._loadedConfigData = configData
            print_debug("[ConfigFile] Config saved to: {}".format(self.configPath))
            
            if os.path.exists(self.configPath):
                with open(self.configPath, 'r') as f:
                    savedContent = f.read()
                print_debug("[ConfigFile] Verified saved content: {}".format(savedContent[:200]))
                return True
            else:
                print_error("[ConfigFile] File was not saved despite no errors")
                return False
            
        except Exception as e:
            print_error("[ConfigFile] Error saving config: {}".format(str(e)))
            return False

    def getLoadedData(self):
        return self._loadedConfigData

    def exists(self):
        exists = os.path.exists(self.configPath)
        print_debug("[ConfigFile] File exists check: {} -> {}".format(self.configPath, exists))
        return exists

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
                print_debug("[ConfigFile] Config backup created: {}".format(backupPath))
                return True
        except Exception as e:
            print_error("[ConfigFile] Error creating config backup: {}".format(str(e)))
        return False

    def restore_config(self, backupSuffix='.backup'):
        try:
            backupPath = self.configPath + backupSuffix
            if os.path.exists(backupPath):
                import shutil
                shutil.copy2(backupPath, self.configPath)
                print_debug("[ConfigFile] Config restored from backup")
                return True
        except Exception as e:
            print_error("[ConfigFile] Error restoring config from backup: {}".format(str(e)))
        return False