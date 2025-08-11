# -*- coding: utf-8 -*-
import json
from gui.modsSettingsApi import g_modsSettingsApi
from .config_param import g_configParams
from .utils import print_debug, print_error, print_log

modLinkage = "com.under_pressure.calculationelo"

def _color_to_hex(color_list):
    try:
        r, g, b = color_list
        return "#{:02x}{:02x}{:02x}".format(r, g, b)
    except:
        return "#ffffff"

def _color_from_hex(hex_color):
    try:
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    except:
        return [255, 255, 255]

class Config:
    def __init__(self):
        self.config_path = './mods/configs/under_pressure/config.json'
        self.settings = None
        self.load_config()
        self.register_mod_settings()

    def register_mod_settings(self):
        try:
            enabled_value = g_configParams.enabled.value
            display_mode_value = next((i for i, opt in enumerate(g_configParams.displayMode.options) if opt.value == g_configParams.displayMode.value), 0)
            hotkey_value = g_configParams.eloHotKey.value
            
            # Конвертація кольорів у hex для ModsSettingsAPI
            panel_bg_color_value = _color_to_hex(g_configParams.panelBackgroundColor.value)
            header_color_value = _color_to_hex(g_configParams.headerColor.value)
            allies_names_color_value = _color_to_hex(g_configParams.alliesNamesColor.value)
            enemies_names_color_value = _color_to_hex(g_configParams.enemiesNamesColor.value)
            allies_rating_color_value = _color_to_hex(g_configParams.alliesRatingColor.value)
            enemies_rating_color_value = _color_to_hex(g_configParams.enemiesRatingColor.value)
            elo_gain_color_value = _color_to_hex(g_configParams.eloGainColor.value)
            elo_loss_color_value = _color_to_hex(g_configParams.eloLossColor.value)
            winrate_color_value = _color_to_hex(g_configParams.winrateColor.value)
            battles_color_value = _color_to_hex(g_configParams.battlesColor.value)
            text_shadow_color_value = _color_to_hex(g_configParams.textShadowColor.value)

            template = {
                'modDisplayName': 'Calculation Elo',
                'enabled': enabled_value,
                'column1': [
                    {'type': 'Label',
                     'text': '\u041e\u0441\u043d\u043e\u0432\u043d\u0456 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u0438'
                    },
                    {
                        'type': 'CheckBox',
                        'text': '\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u043c\u043e\u0434',
                        'value': enabled_value,
                        'varName': 'enabled',
                        'tooltip': '{HEADER}\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u043c\u043e\u0434{/HEADER}{BODY}\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u0430\u0431\u043e \u0432\u0438\u043c\u043a\u043d\u0443\u0442\u0438 \u0432\u0435\u0441\u044c \u043c\u043e\u0434.{/BODY}'
                    },
                    {
                        'type': 'Dropdown',
                        'text': '\u0420\u0435\u0436\u0438\u043c \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f',
                        'value': display_mode_value,
                        'options': [
                            {'label': opt.displayName}
                            for opt in g_configParams.displayMode.options
                        ],
                        'varName': 'display-mode',
                        'tooltip': '{HEADER}\u0420\u0435\u0436\u0438\u043c \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f{/HEADER}{BODY}Always - \u0417\u0430\u0432\u0436\u0434\u0438 \u043f\u043e\u043a\u0430\u0437\u0443\u0432\u0430\u0442\u0438, On HotKey Pressed - \u041f\u0440\u0438 \u0437\u0430\u0442\u0438\u0441\u043a\u0430\u043d\u043d\u0456 \u043a\u043b\u0430\u0432\u0456\u0448\u0456.{/BODY}'
                    },
                    {
                        'type': 'HotKey',
                        'text': '\u041a\u043b\u0430\u0432\u0456\u0448\u0430 \u0434\u043b\u044f \u043f\u043e\u043a\u0430\u0437\u0443 \u043f\u0430\u043d\u0435\u043b\u0456',
                        'value': hotkey_value,
                        'varName': 'elo-hotkey',
                        'tooltip': '{HEADER}\u041a\u043b\u0430\u0432\u0456\u0448\u0430{/HEADER}{BODY}\u0412\u0438\u0431\u0435\u0440\u0456\u0442\u044c \u0431\u0443\u0434\u044c-\u044f\u043a\u0443 \u043a\u043b\u0430\u0432\u0456\u0448\u0443 \u0434\u043b\u044f \u043f\u043e\u043a\u0430\u0437\u0443 \u043f\u0430\u043d\u0435\u043b\u0456.{/BODY}'
                    },
                    {'type': 'Label',
                     'text': '\u0412\u0438\u0434\u0438\u043c\u0456\u0441\u0442\u044c \u0435\u043b\u0435\u043c\u0435\u043d\u0442\u0456\u0432'
                    },
                    {
                        'type': 'CheckBox',
                        'text': '\u041f\u043e\u043a\u0430\u0437\u0443\u0432\u0430\u0442\u0438 \u0456\u043c\u0435\u043d\u0430 \u0433\u0440\u0430\u0432\u0446\u0456\u0432',
                        'value': g_configParams.showPlayerNames.value,
                        'varName': 'show-player-names',
                        'tooltip': '{HEADER}\u0406\u043c\u0435\u043d\u0430 \u0433\u0440\u0430\u0432\u0446\u0456\u0432{/HEADER}{BODY}\u0412\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u0438 \u0456\u043c\u0435\u043d\u0430 \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432 \u0456 \u0432\u043e\u0440\u043e\u0433\u0456\u0432.{/BODY}'
                    },
                    {
                        'type': 'CheckBox',
                        'text': '\u041f\u043e\u043a\u0430\u0437\u0443\u0432\u0430\u0442\u0438 \u0437\u043c\u0456\u043d\u0438 Elo',
                        'value': g_configParams.showEloChanges.value,
                        'varName': 'show-elo-changes',
                        'tooltip': '{HEADER}\u0417\u043c\u0456\u043d\u0438 Elo{/HEADER}{BODY}\u0412\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u0438 +/- Elo \u0437\u0430 \u043f\u0435\u0440\u0435\u043c\u043e\u0433\u0443/\u043f\u043e\u0440\u0430\u0437\u043a\u0443.{/BODY}'
                    },
                    {
                        'type': 'CheckBox',
                        'text': '\u041f\u043e\u043a\u0430\u0437\u0443\u0432\u0430\u0442\u0438 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0443',
                        'value': g_configParams.showWinrateAndBattles.value,
                        'varName': 'show-winrate-battles',
                        'tooltip': '{HEADER}\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430{/HEADER}{BODY}\u0412\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u0438 \u0432\u0456\u0434\u0441\u043e\u0442\u043e\u043a \u043f\u0435\u0440\u0435\u043c\u043e\u0433 \u0456 \u043a\u0456\u043b\u044c\u043a\u0456\u0441\u0442\u044c \u0431\u043e\u0457\u0432.{/BODY}'
                    },
                    {'type': 'Label',
                     'text': '\u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u043f\u0430\u043d\u0435\u043b\u0456'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0444\u043e\u043d\u0443 \u043f\u0430\u043d\u0435\u043b\u0456',
                        'value': panel_bg_color_value,
                        'varName': 'panel-background-color',
                        'tooltip': '{HEADER}\u0424\u043e\u043d \u043f\u0430\u043d\u0435\u043b\u0456{/HEADER}{BODY}\u0412\u0438\u0431\u0435\u0440\u0456\u0442\u044c \u043a\u043e\u043b\u0456\u0440 \u0444\u043e\u043d\u0443 \u0434\u043b\u044f \u043f\u0430\u043d\u0435\u043b\u0456.{/BODY}'
                    },
                    {
                        'type': 'Slider',
                        'text': '\u041f\u0440\u043e\u0437\u043e\u0440\u0456\u0441\u0442\u044c \u0444\u043e\u043d\u0443',
                        'value': int(g_configParams.panelBackgroundAlpha.value * 100),
                        'minimum': 0,
                        'maximum': 100,
                        'varName': 'panel-background-alpha',
                        'tooltip': '{HEADER}\u041f\u0440\u043e\u0437\u043e\u0440\u0456\u0441\u0442\u044c{/HEADER}{BODY}\u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u043f\u0440\u043e\u0437\u043e\u0440\u043e\u0441\u0442\u0456 \u0444\u043e\u043d\u0443 \u043f\u0430\u043d\u0435\u043b\u0456.{/BODY}'
                    }
                ],
                'column2': [
                    {'type': 'Label',
                     'text': '\u041a\u043e\u043b\u044c\u043e\u0440\u0438 \u0435\u043b\u0435\u043c\u0435\u043d\u0442\u0456\u0432'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0430',
                        'value': header_color_value,
                        'varName': 'header-color',
                        'tooltip': '{HEADER}\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0430 "-=Elo=-".{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0456\u043c\u0435\u043d \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432',
                        'value': allies_names_color_value,
                        'varName': 'allies-names-color',
                        'tooltip': '{HEADER}\u0406\u043c\u0435\u043d\u0430 \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u0456\u043c\u0435\u043d \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0456\u043c\u0435\u043d \u0432\u043e\u0440\u043e\u0433\u0456\u0432',
                        'value': enemies_names_color_value,
                        'varName': 'enemies-names-color',
                        'tooltip': '{HEADER}\u0406\u043c\u0435\u043d\u0430 \u0432\u043e\u0440\u043e\u0433\u0456\u0432{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u0456\u043c\u0435\u043d \u0432\u043e\u0440\u043e\u0433\u0456\u0432.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0443 \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432',
                        'value': allies_rating_color_value,
                        'varName': 'allies-rating-color',
                        'tooltip': '{HEADER}\u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0443 \u0441\u043e\u044e\u0437\u043d\u0438\u043a\u0456\u0432.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0443 \u0432\u043e\u0440\u043e\u0433\u0456\u0432',
                        'value': enemies_rating_color_value,
                        'varName': 'enemies-rating-color',
                        'tooltip': '{HEADER}\u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u0432\u043e\u0440\u043e\u0433\u0456\u0432{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0443 \u0432\u043e\u0440\u043e\u0433\u0456\u0432.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u043f\u0440\u0438\u0440\u043e\u0441\u0442\u0443 Elo',
                        'value': elo_gain_color_value,
                        'varName': 'elo-gain-color',
                        'tooltip': '{HEADER}\u041f\u0440\u0438\u0440\u0456\u0441\u0442 Elo{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u043f\u043e\u0437\u0438\u0442\u0438\u0432\u043d\u043e\u0457 \u0437\u043c\u0456\u043d\u0438 Elo.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0432\u0442\u0440\u0430\u0442\u0438 Elo',
                        'value': elo_loss_color_value,
                        'varName': 'elo-loss-color',
                        'tooltip': '{HEADER}\u0412\u0442\u0440\u0430\u0442\u0430 Elo{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u043d\u0435\u0433\u0430\u0442\u0438\u0432\u043d\u043e\u0457 \u0437\u043c\u0456\u043d\u0438 Elo.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0432\u0456\u0434\u0441\u043e\u0442\u043a\u0430 \u043f\u0435\u0440\u0435\u043c\u043e\u0433',
                        'value': winrate_color_value,
                        'varName': 'winrate-color',
                        'tooltip': '{HEADER}\u0412\u0456\u0434\u0441\u043e\u0442\u043e\u043a \u043f\u0435\u0440\u0435\u043c\u043e\u0433{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u0432\u0456\u0434\u0441\u043e\u0442\u043a\u0430 \u043f\u0435\u0440\u0435\u043c\u043e\u0433.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u043a\u0456\u043b\u044c\u043a\u043e\u0441\u0442\u0456 \u0431\u043e\u0457\u0432',
                        'value': battles_color_value,
                        'varName': 'battles-color',
                        'tooltip': '{HEADER}\u041a\u0456\u043b\u044c\u043a\u0456\u0441\u0442\u044c \u0431\u043e\u0457\u0432{/HEADER}{BODY}\u041a\u043e\u043b\u0456\u0440 \u0434\u043b\u044f \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u043a\u0456\u043b\u044c\u043a\u043e\u0441\u0442\u0456 \u0431\u043e\u0457\u0432.{/BODY}'
                    },
                    {'type': 'Label',
                     'text': '\u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u0442\u0456\u043d\u0456'
                    },
                    {
                        'type': 'CheckBox',
                        'text': '\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u0442\u0456\u043d\u044c \u0442\u0435\u043a\u0441\u0442\u0443',
                        'value': g_configParams.textShadowEnabled.value,
                        'varName': 'text-shadow-enabled',
                        'tooltip': '{HEADER}\u0422\u0456\u043d\u044c \u0442\u0435\u043a\u0441\u0442\u0443{/HEADER}{BODY}\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u0430\u0431\u043e \u0432\u0438\u043c\u043a\u043d\u0443\u0442\u0438 \u0442\u0456\u043d\u044c \u0434\u043b\u044f \u0442\u0435\u043a\u0441\u0442\u0443.{/BODY}'
                    },
                    {
                        'type': 'ColorChoice',
                        'text': '\u041a\u043e\u043b\u0456\u0440 \u0442\u0456\u043d\u0456',
                        'value': text_shadow_color_value,
                        'varName': 'text-shadow-color',
                        'tooltip': '{HEADER}\u041a\u043e\u043b\u0456\u0440 \u0442\u0456\u043d\u0456{/HEADER}{BODY}\u0412\u0438\u0431\u0435\u0440\u0456\u0442\u044c \u043a\u043e\u043b\u0456\u0440 \u0442\u0456\u043d\u0456 \u0434\u043b\u044f \u0442\u0435\u043a\u0441\u0442\u0443.{/BODY}'
                    },
                    {
                        'type': 'Slider',
                        'text': '\u041f\u0440\u043e\u0437\u043e\u0440\u0456\u0441\u0442\u044c \u0442\u0456\u043d\u0456',
                        'value': int(g_configParams.textShadowAlpha.value * 100),
                        'minimum': 0,
                        'maximum': 100,
                        'varName': 'text-shadow-alpha',
                        'tooltip': '{HEADER}\u041f\u0440\u043e\u0437\u043e\u0440\u0456\u0441\u0442\u044c \u0442\u0456\u043d\u0456{/HEADER}{BODY}\u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u043f\u0440\u043e\u0437\u043e\u0440\u043e\u0441\u0442\u0456 \u0442\u0456\u043d\u0456 \u0442\u0435\u043a\u0441\u0442\u0443.{/BODY}'
                    },
                    {
                        'type': 'Slider',
                        'text': '\u0412\u0456\u0434\u0441\u0442\u0430\u043d\u044c \u0442\u0456\u043d\u0456',
                        'value': int(g_configParams.textShadowDistance.value),
                        'minimum': 0,
                        'maximum': 10,
                        'varName': 'text-shadow-distance',
                        'tooltip': '{HEADER}\u0412\u0456\u0434\u0441\u0442\u0430\u043d\u044c \u0442\u0456\u043d\u0456{/HEADER}{BODY}\u0412\u0456\u0434\u0441\u0442\u0430\u043d\u044c \u0442\u0456\u043d\u0456 \u0432\u0456\u0434 \u0442\u0435\u043a\u0441\u0442\u0443.{/BODY}'
                    },
                    {
                        'type': 'Slider',
                        'text': '\u0420\u043e\u0437\u043c\u0438\u0442\u0442\u044f \u0442\u0456\u043d\u0456',
                        'value': int(g_configParams.textShadowBlur.value),
                        'minimum': 0,
                        'maximum': 10,
                        'varName': 'text-shadow-blur',
                        'tooltip': '{HEADER}\u0420\u043e\u0437\u043c\u0438\u0442\u0442\u044f \u0442\u0456\u043d\u0456{/HEADER}{BODY}\u0420\u043e\u0437\u043c\u0438\u0442\u0442\u044f \u0435\u0444\u0435\u043a\u0442\u0443 \u0442\u0456\u043d\u0456.{/BODY}'
                    },
                    {'type': 'Label',
                     'text': '\u0406\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0456\u044f \u043f\u0440\u043e \u0444\u0430\u0439\u043b \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u0457',
                     'tooltip': '{HEADER}\u0424\u0430\u0439\u043b \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u0457{/HEADER}{BODY}\u0424\u0430\u0439\u043b \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u0457 \u0437\u043d\u0430\u0445\u043e\u0434\u0438\u0442\u044c\u0441\u044f \u0432 \u043f\u0430\u043f\u0446\u0456 [\u041f\u0430\u043f\u043a\u0430 \u0456\u0437 \u0433\u0440\u043e\u044e]\\mods\\configs\\under_pressure \u043f\u0456\u0434 \u043d\u0430\u0437\u0432\u043e\u044e config.json. \n\u042f\u043a\u0449\u043e \u0432\u0438 \u0445\u043e\u0447\u0435\u0442\u0435 \u0437\u0433\u0435\u043d\u0435\u0440\u0443\u0432\u0430\u0442\u0438 \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u044e \u043f\u043e \u0437\u0430\u043c\u043e\u0432\u0447\u0443\u0432\u0430\u043d\u043d\u044e \u0442\u043e \u0432\u0438\u0434\u0430\u043b\u0456\u0442\u044c \u0434\u0430\u043d\u0438\u0439 \u0444\u0430\u0439\u043b \u0456 \u043f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u0442\u0456\u0442\u044c \u0433\u0440\u0443. \u0422\u0430\u043a\u043e\u0436 \u0444\u0430\u0439\u043b \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u0457 \u043c\u043e\u0436\u043d\u0430 \u0440\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0432\u0440\u0443\u0447\u043d\u0443.{/BODY}'
                    }
                ] 
            }

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
            for tokenName, value in newSettings.items():
                if tokenName in g_configParams.items():
                    param = g_configParams.items()[tokenName]
                    
                    # Спеціальна обробка для кольорів
                    if 'color' in tokenName and isinstance(value, basestring):
                        param.value = _color_from_hex(value)
                    # Спеціальна обробка для слайдерів з відсотками
                    elif tokenName in ['panel-background-alpha', 'text-shadow-alpha']:
                        param.value = float(value) / 100.0
                    # Звичайна обробка
                    elif hasattr(param, 'msaValue'):
                        param.msaValue = value
                    else:
                        param.value = value
                        
            self.save_config()
            
            # Оновлення інтерфейсу після зміни налаштувань
            from . import g_multiTextPanel
            if g_multiTextPanel:
                g_multiTextPanel.refresh_colors_and_effects()
                g_multiTextPanel.update_hotkeys()
                
                # Перевірка чи змінилась видимість елементів
                visibility_params = ['show-player-names', 'show-elo-changes', 'show-winrate-battles']
                if any(param in newSettings for param in visibility_params):
                    g_multiTextPanel.recreate_components_with_visibility_changes()
                
            print_debug("Settings updated successfully")
        except Exception as e:
            print_error("Error updating settings: %s" % str(e))

    def save_config(self):
        try:
            import os
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            config_data = {}
            for tokenName, param in g_configParams.items().items():
                config_data[tokenName] = param.value

            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print_debug("Config saved successfully")
        except Exception as e:
            print_error("Error saving config: %s" % str(e))

    def load_config(self):
        try:
            import os
            if not os.path.exists(self.config_path):
                print_debug("Config file not found, using defaults")
                return
                
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                
            for tokenName, value in config_data.items():
                if tokenName in g_configParams.items():
                    param = g_configParams.items()[tokenName]
                    param.value = value
                    
            print_debug("Config loaded successfully")
        except Exception as e:
            print_debug("Config file not found or invalid, using defaults: %s" % str(e))

    def sync_with_msa(self):
        try:
            if self.settings:
                current_config = {}
                for tokenName, param in g_configParams.items().items():
                    # Конвертація кольорів для MSA
                    if 'color' in tokenName:
                        current_config[tokenName] = _color_to_hex(param.value)
                    # Конвертація слайдерів з відсотками
                    elif tokenName in ['panel-background-alpha', 'text-shadow-alpha']:
                        current_config[tokenName] = int(param.value * 100)
                    # Звичайні значення
                    elif hasattr(param, 'msaValue'):
                        current_config[tokenName] = param.msaValue
                    else:
                        current_config[tokenName] = param.value
                        
                g_modsSettingsApi.updateModSettings(modLinkage, current_config)
                print_debug("Config synchronized with ModsSettingsAPI")
        except Exception as e:
            print_error("Error synchronizing config with MSA: %s" % str(e))

g_config = Config()