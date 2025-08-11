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

    def _get_safe_msa_value(self, param):
        try:
            if hasattr(param, 'msaValue') and param.msaValue is not None:
                return param.msaValue
            else:
                return param.toMsaValue(param.value)
        except Exception as e:
            print_error("Error getting msaValue for %s: %s" % (param.tokenName, str(e)))
            return param.toMsaValue(param.defaultValue)

    def _register_mod(self):
        try:
            # Отримання значень параметрів
            enabled_value = bool(g_configParams.enabled.value)
            display_mode_value = self._get_safe_msa_value(g_configParams.displayMode)
            hotkey_value = self._get_safe_msa_value(g_configParams.eloHotKey)
            allies_color_value = self._get_safe_msa_value(g_configParams.alliesColor)
            enemies_color_value = self._get_safe_msa_value(g_configParams.enemiesColor)
            additional_color_value = self._get_safe_msa_value(g_configParams.additionalColor)
            elo_visible_value = self._get_safe_msa_value(g_configParams.eloVisible)
            enemies_for_28_days_visible_value = self._get_safe_msa_value(g_configParams.enemiesFor28DaysVisible)
            
            # Позиція та розмір
            panel_x_value = self._get_safe_msa_value(g_configParams.panelX)
            panel_y_value = self._get_safe_msa_value(g_configParams.panelY)
            panel_width_value = self._get_safe_msa_value(g_configParams.panelWidth)
            panel_height_value = self._get_safe_msa_value(g_configParams.panelHeight)
            panel_alpha_value = self._get_safe_msa_value(g_configParams.panelAlpha)
            font_size_value = self._get_safe_msa_value(g_configParams.fontSize)
            show_border_value = self._get_safe_msa_value(g_configParams.showBorder)

            template = {
                'modDisplayName': 'Калькулятор Ело',
                'enabled': enabled_value,
                'settingsCache': True,
                'settings': [
                    # Заголовок - Основні налаштування
                    {
                        'type': 'Label',
                        'text': 'Основні налаштування',
                        'pos': {'x': 50, 'y': 50},
                        'size': {'width': 300, 'height': 30},
                        'color': '0xFFFF00'
                    },
                    
                    # Увімкнення/вимкнення мода
                    {
                        'type': 'CheckBox',
                        'varName': 'enabled',
                        'value': enabled_value,
                        'text': 'Увімкнути мод',
                        'tooltip': 'Увімкнути/вимкнути мод',
                        'pos': {'x': 70, 'y': 90},
                        'size': {'width': 200, 'height': 30}
                    },
                    
                    # Режим відображення
                    {
                        'type': 'DropDown',
                        'varName': 'displayMode',
                        'value': display_mode_value,
                        'text': 'Режим відображення',
                        'tooltip': 'Коли показувати панель ELO',
                        'pos': {'x': 70, 'y': 130},
                        'size': {'width': 250, 'height': 30},
                        'options': [
                            {'text': 'Завжди', 'value': 0},
                            {'text': 'При натисканні клавіші', 'value': 1}
                        ]
                    },
                    
                    # Заголовок - Видимість елементів
                    {
                        'type': 'Label',
                        'text': 'Видимість елементів',
                        'pos': {'x': 50, 'y': 190},
                        'size': {'width': 300, 'height': 30},
                        'color': '0xFFFF00'
                    },
                    
                    # Показувати ELO
                    {
                        'type': 'CheckBox',
                        'varName': 'eloVisible',
                        'value': elo_visible_value,
                        'text': 'Показувати зміни ELO',
                        'tooltip': 'Відображати зміни рейтингу ELO',
                        'pos': {'x': 70, 'y': 230},
                        'size': {'width': 250, 'height': 30}
                    },
                    
                    # Показувати статистику за 28 днів
                    {
                        'type': 'CheckBox',
                        'varName': 'enemiesFor28DaysVisible',
                        'value': enemies_for_28_days_visible_value,
                        'text': 'Показувати статистику за 28 днів',
                        'tooltip': 'Відображати статистику ворогів за останні 28 днів',
                        'pos': {'x': 70, 'y': 270},
                        'size': {'width': 280, 'height': 30}
                    },
                    
                    # Заголовок - Кольори
                    {
                        'type': 'Label',
                        'text': 'Налаштування кольорів',
                        'pos': {'x': 50, 'y': 330},
                        'size': {'width': 300, 'height': 30},
                        'color': '0xFFFF00'
                    },
                    
                    # Колір союзників
                    {
                        'type': 'ColorPicker',
                        'varName': 'alliesColor',
                        'value': allies_color_value,
                        'text': 'Колір союзників',
                        'tooltip': 'Колір тексту для союзників',
                        'pos': {'x': 70, 'y': 370},
                        'size': {'width': 200, 'height': 30}
                    },
                    
                    # Колір ворогів
                    {
                        'type': 'ColorPicker',
                        'varName': 'enemiesColor',
                        'value': enemies_color_value,
                        'text': 'Колір ворогів',
                        'tooltip': 'Колір тексту для ворогів',
                        'pos': {'x': 70, 'y': 410},
                        'size': {'width': 200, 'height': 30}
                    },
                    
                    # Додатковий колір
                    {
                        'type': 'ColorPicker',
                        'varName': 'additionalColor',
                        'value': additional_color_value,
                        'text': 'Колір додаткової інформації',
                        'tooltip': 'Колір для ELO та статистики',
                        'pos': {'x': 70, 'y': 450},
                        'size': {'width': 250, 'height': 30}
                    },
                    
                    # Заголовок - Позиція та розмір
                    {
                        'type': 'Label',
                        'text': 'Позиція та розмір панелі',
                        'pos': {'x': 400, 'y': 50},
                        'size': {'width': 300, 'height': 30},
                        'color': '0xFFFF00'
                    },
                    
                    # Позиція X
                    {
                        'type': 'Slider',
                        'varName': 'panelX',
                        'value': panel_x_value,
                        'text': 'Позиція X',
                        'tooltip': 'Горизонтальна позиція панелі',
                        'pos': {'x': 420, 'y': 90},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 0, 'max': 1920, 'step': 10}
                    },
                    
                    # Позиція Y
                    {
                        'type': 'Slider',
                        'varName': 'panelY',
                        'value': panel_y_value,
                        'text': 'Позиція Y',
                        'tooltip': 'Вертикальна позиція панелі',
                        'pos': {'x': 420, 'y': 130},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 0, 'max': 1080, 'step': 10}
                    },
                    
                    # Ширина панелі
                    {
                        'type': 'Slider',
                        'varName': 'panelWidth',
                        'value': panel_width_value,
                        'text': 'Ширина панелі',
                        'tooltip': 'Ширина панелі ELO',
                        'pos': {'x': 420, 'y': 170},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 100, 'max': 500, 'step': 10}
                    },
                    
                    # Висота панелі
                    {
                        'type': 'Slider',
                        'varName': 'panelHeight',
                        'value': panel_height_value,
                        'text': 'Висота панелі',
                        'tooltip': 'Висота панелі ELO',
                        'pos': {'x': 420, 'y': 210},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 80, 'max': 300, 'step': 10}
                    },
                    
                    # Прозорість панелі
                    {
                        'type': 'Slider',
                        'varName': 'panelAlpha',
                        'value': panel_alpha_value,
                        'text': 'Прозорість фону',
                        'tooltip': 'Прозорість фону панелі (0.0 - прозорий, 1.0 - непрозорий)',
                        'pos': {'x': 420, 'y': 250},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 0.0, 'max': 1.0, 'step': 0.1}
                    },
                    
                    # Розмір шрифту
                    {
                        'type': 'Slider',
                        'varName': 'fontSize',
                        'value': font_size_value,
                        'text': 'Розмір шрифту',
                        'tooltip': 'Розмір шрифту тексту',
                        'pos': {'x': 420, 'y': 290},
                        'size': {'width': 250, 'height': 30},
                        'range': {'min': 8, 'max': 24, 'step': 1}
                    },
                    
                    # Показувати рамку
                    {
                        'type': 'CheckBox',
                        'varName': 'showBorder',
                        'value': show_border_value,
                        'text': 'Показувати рамку',
                        'tooltip': 'Відображати рамку навколо панелі',
                        'pos': {'x': 420, 'y': 330},
                        'size': {'width': 200, 'height': 30}
                    },
                    
                    # Інформація про файл конфігурації
                    {
                        'type': 'Label',
                        'text': 'Файл конфігурації також можна редагувати вручну.',
                        'pos': {'x': 50, 'y': 520},
                        'size': {'width': 400, 'height': 20},
                        'color': '0xCCCCCC'
                    },
                    {
                        'type': 'Label',
                        'text': 'Розташування: [WoT]/mods/configs/under_pressure/config.json',
                        'pos': {'x': 50, 'y': 540},
                        'size': {'width': 500, 'height': 20},
                        'color': '0xCCCCCC'
                    }
                ]
            }

            # Реєстрація в ModsSettingsAPI
            current_settings = g_modsSettingsApi.getModSettings(modLinkage, template)
            
            if current_settings is None:
                self.settings = g_modsSettingsApi.setModTemplate(
                    modLinkage,
                    template,
                    self.on_settings_changed,
                    self.on_button_clicked
                )
            else:
                self.settings = current_settings
                g_modsSettingsApi.registerCallback(
                    modLinkage,
                    self.on_settings_changed,
                    self.on_button_clicked
                )
                
            print_debug("Mod registered in ModsSettingsAPI")
            
        except Exception as e:
            print_error("Failed to register mod: %s" % str(e))

    def on_button_clicked(self, linkage, varName, value):
        if linkage != modLinkage:
            return
        print_debug("Button clicked: %s = %s" % (varName, value))

    def on_settings_changed(self, linkage, newSettings):
        if linkage != modLinkage:
            return
        try:
            print_debug("Settings changed: %s" % str(newSettings))
            
            for tokenName, value in newSettings.items():
                if tokenName in g_configParams.items():
                    param = g_configParams.items()[tokenName]
                    # Конвертація значення з MSA формату
                    param.value = param.fromMsaValue(value)
                    param.msaValue = value
                    print_debug("Updated %s: %s (msa: %s)" % (tokenName, param.value, value))
            
            self.save_config()
            
            # Оповістити multiTextPanel про зміни
            self._notify_panel_changes()
            
            print_debug("Settings updated successfully")
            
        except Exception as e:
            print_error("Error updating settings: %s" % str(e))

    def _notify_panel_changes(self):
        """Оповіщення панелі про зміни конфігурації"""
        try:
            from . import g_multiTextPanel
            if g_multiTextPanel:
                g_multiTextPanel.update_hotkeys()
                g_multiTextPanel.update_panel_settings()
                print_debug("Panel notified about config changes")
        except Exception as e:
            print_debug("Could not notify panel about changes: %s" % str(e))

    def sync_with_msa(self):
        """Синхронізація значень з ModsSettingsAPI"""
        try:
            if hasattr(self, 'settings') and self.settings:
                current_settings = g_modsSettingsApi.getModSettings(modLinkage, None)
                if current_settings:
                    self.on_settings_changed(modLinkage, current_settings)
                    print_debug("Config synced with MSA")
        except Exception as e:
            print_debug("Could not sync with MSA: %s" % str(e))

    def save_config(self):
        try:
            config_data = {}
            for tokenName, param in g_configParams.items().items():
                config_data[tokenName] = param.value

            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print_debug("Config saved successfully")
        except Exception as e:
            print_error("Error saving config: %s" % str(e))

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                for tokenName, value in config_data.items():
                    if tokenName in g_configParams.items():
                        param = g_configParams.items()[tokenName]
                        param.value = param.fromJsonValue(value)
                        print_debug("Loaded %s: %s" % (tokenName, param.value))
                
                print_debug("Config loaded successfully")
            else:
                print_debug("Config file does not exist, using defaults")
                
        except Exception as e:
            print_error("Error loading config: %s" % str(e))

g_config = None