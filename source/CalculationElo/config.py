# -*- coding: utf-8 -*-
import json
import os
from gui.modsSettingsApi import g_modsSettingsApi
from .utils import print_log, print_error, print_debug
from .config_param import g_configParams

modLinkage = 'me.under-pressure.calculationelo'

class Config(object):
    def __init__(self):
        self.config_path = os.path.join('mods', 'configs', 'under_pressure', 'config.json')
        self._ensure_config_exists()
        self.load_config()
        self._register_mod()

    def _ensure_config_exists(self):
        try:
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                print_debug("Created config directory")

            if not os.path.exists(self.config_path):
                self._create_default_config()
        except Exception as e:
            print_error("Error ensuring config exists: %s" % str(e))

    def _create_default_config(self):
        try:
            config_data = {}
            for tokenName, param in g_configParams.items().items():
                config_data[tokenName] = param.defaultValue

            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print_debug("Created default config file")
        except Exception as e:
            print_error("Error creating default config: %s" % str(e))

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                for tokenName, param in g_configParams.items().items():
                    if tokenName in config_data:
                        try:
                            param.jsonValue = config_data[tokenName]
                        except Exception as e:
                            print_error("Error loading parameter %s: %s" % (tokenName, str(e)))
                            param.value = param.defaultValue
                    else:
                        param.value = param.defaultValue
                        
                print_debug("Config loaded successfully")
            else:
                print_debug("Config file not found, using defaults")
        except Exception as e:
            print_error("Error loading config: %s" % str(e))

    def save_config(self):
        try:
            config_data = {}
            for tokenName, param in g_configParams.items().items():
                config_data[tokenName] = param.jsonValue

            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print_debug("Config saved successfully")
        except Exception as e:
            print_error("Error saving config: %s" % str(e))

    def _get_safe_msa_value(self, param):
        try:
            if hasattr(param, 'msaValue'):
                return param.msaValue
            else:
                return param.value
        except Exception as e:
            print_error("Error getting msaValue for %s: %s" % (param.tokenName, str(e)))
            return param.defaultValue

    def _register_mod(self):
        try:
            template = {
                'modDisplayName': u'Калькулятор Ело',
                'enabled': g_configParams.enabled.defaultMsaValue,
                'column1': [
                    {
                        'type': 'Label',
                        'text': u'Основні налаштування'
                    },
                    {
                        'type': 'Dropdown',
                        'text': u'Режим відображення',
                        'value': g_configParams.displayMode.defaultMsaValue,
                        'varName': 'display-mode',
                        'options': [
                            {'label': u'Завжди показувати'},
                            {'label': u'Показувати при натисканні клавіші'}
                        ],
                        'tooltip': u'{HEADER}Режим відображення{/HEADER}{BODY}Вибирати коли показувати панель з інформацією{/BODY}'
                    },
                    {
                        'type': 'HotKey',
                        'text': u'Гаряча клавіша',
                        'value': g_configParams.eloHotKey.defaultMsaValue,
                        'varName': 'elo-hotkey',
                        'tooltip': u'{HEADER}Гаряча клавіша{/HEADER}{BODY}Клавіша для показу панелі у режимі "По натисканню"{/BODY}'
                    },
                    {
                        'type': 'Label',
                        'text': u'Налаштування видимості'
                    },
                    {
                        'type': 'CheckBox',
                        'text': u'Показувати заголовок',
                        'value': g_configParams.showTitleVisible.defaultMsaValue,
                        'varName': 'show-title-visible',
                        'tooltip': u'{HEADER}Показувати заголовок{/HEADER}{BODY}Показувати заголовок "-=Elo=-" у панелі{/BODY}'
                    },
                    {
                        'type': 'CheckBox',
                        'text': u'Показувати назви команд',
                        'value': g_configParams.showTeamNames.defaultMsaValue,
                        'varName': 'show-team-names',
                        'tooltip': u'{HEADER}Показувати назви команд{/HEADER}{BODY}Показувати скорочені назви команд союзників та ворогів{/BODY}'
                    },
                    {
                        'type': 'CheckBox',
                        'text': u'Показувати зміни Elo',
                        'value': g_configParams.showEloChanges.defaultMsaValue,
                        'varName': 'show-elo-changes',
                        'tooltip': u'{HEADER}Показувати зміни Elo{/HEADER}{BODY}Показувати можливі зміни рейтингу за перемогу/поразку{/BODY}'
                    },
                    {
                        'type': 'CheckBox',
                        'text': u'Показувати статистику боїв суперника',
                        'value': g_configParams.showWinrateAndBattles.defaultMsaValue,
                        'varName': 'show-winrate-and-battles',
                        'tooltip': u'{HEADER}Показувати статистику{/HEADER}{BODY}Показувати відсоток перемог та кількість боїв суперника{/BODY}'
                    }
                ],
                'column2': [
                            {
                                'type': 'Label',
                                'text': u'Налаштування кольорів'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір заголовка',
                                'value': g_configParams.headerColor.defaultMsaValue,
                                'varName': 'header-color',
                                'tooltip': u'{HEADER}Колір заголовка{/HEADER}{BODY}Колір тексту заголовка панелі{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір назв союзників',
                                'value': g_configParams.alliesNamesColor.defaultMsaValue,
                                'varName': 'allies-names-color',
                                'tooltip': u'{HEADER}Колір назв союзників{/HEADER}{BODY}Колір для відображення назви команди союзників{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір назв ворогів',
                                'value': g_configParams.enemiesNamesColor.defaultMsaValue,
                                'varName': 'enemies-names-color',
                                'tooltip': u'{HEADER}Колір назв ворогів{/HEADER}{BODY}Колір для відображення назви команди ворогів{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір рейтингу союзників',
                                'value': g_configParams.alliesRatingColor.defaultMsaValue,
                                'varName': 'allies-rating-color',
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір рейтингу ворогів',
                                'value': g_configParams.enemiesRatingColor.defaultMsaValue,
                                'varName': 'enemies-rating-color',
                                'tooltip': u'{HEADER}Колір рейтингу ворогів{/HEADER}{BODY}Колір для відображення рейтингу команди ворогів{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір приросту Elo',
                                'value': g_configParams.eloGainColor.defaultMsaValue,
                                'varName': 'elo-gain-color',
                                'tooltip': u'{HEADER}Колір приросту Elo{/HEADER}{BODY}Колір для відображення можливого приросту рейтингу{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір втрати Elo',
                                'value': g_configParams.eloLossColor.defaultMsaValue,
                                'varName': 'elo-loss-color',
                                'tooltip': u'{HEADER}Колір втрати Elo{/HEADER}{BODY}Колір для відображення можливої втрати рейтингу{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір відсотка перемог',
                                'value': g_configParams.winrateColor.defaultMsaValue,
                                'varName': 'winrate-color',
                                'tooltip': u'{HEADER}Колір відсотка перемог{/HEADER}{BODY}Колір для відображення відсотка перемог{/BODY}'
                            },
                            {
                                'type': 'ColorChoice',
                                'text': u'Колір кількості боїв',
                                'value': g_configParams.battlesColor.defaultMsaValue,
                                'varName': 'battles-color',
                                'tooltip': u'{HEADER}Колір кількості боїв{/HEADER}{BODY}Колір для відображення кількості боїв{/BODY}'
                            }
                        ]
                    }

            g_modsSettingsApi.setModTemplate(modLinkage, template, self.on_settings_changed)
            print_debug("Mod template registered successfully using setModTemplate")
            
        except Exception as e:
            print_error("Error registering mod template: %s" % str(e))

    def on_settings_changed(self, linkage, newSettings):
        """Callback для зміни налаштувань через MSA"""
        if linkage != modLinkage:
            return
        try:
            print_debug("MSA settings changed: %s" % str(newSettings))
            
            for tokenName, value in newSettings.items():
                if tokenName in g_configParams.items():
                    param = g_configParams.items()[tokenName]
                    if hasattr(param, 'fromMsaValue'):
                        param.value = param.fromMsaValue(value)
                    elif hasattr(param, 'msaValue'):
                        param.msaValue = value
                    else:
                        param.value = value
            self.save_config()
            
            self._notify_config_changed()
            
            print_debug("Settings updated successfully")
        except Exception as e:
            print_error("Error updating settings from MSA: %s" % str(e))

    def _notify_config_changed(self):
        """Повідомляє інші компоненти про зміни конфігурації"""
        try:
            from . import g_arenaInfoProvider
            if g_arenaInfoProvider and hasattr(g_arenaInfoProvider, 'on_config_changed'):
                g_arenaInfoProvider.on_config_changed()
                print_debug("Config change notification sent")
        except Exception as e:
            print_error("Error notifying config change: %s" % str(e))

    def sync_with_msa(self):
        """Синхронізація з ModsSettingsApi"""
        try:
            print_debug("MSA sync called - using config file values")
        except Exception as e:
            print_error("Error in MSA sync: %s" % str(e))

g_config = Config()