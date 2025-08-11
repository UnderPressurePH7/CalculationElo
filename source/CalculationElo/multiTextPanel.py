# -*- coding: utf-8 -*-
import BigWorld
import Keys
from gui import InputHandler
from gui.shared.utils.key_mapping import getBigworldNameFromKey

from gui.mods.gambiter import g_guiFlash, utils
from gui.mods.gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, g_guiCache

from .config_param import g_configParams
from .utils import print_log, print_error, print_debug
from . import *

class MultiTextPanel:

    utils.IS_DEBUG = False

    def __init__(self):
        print_debug("[MultiTextPanel] Initializing...")
        self.img_battle = '<img height="14px" width="14px" src="https://cdn-icons-png.flaticon.com/512/1643/1643160.png"/>'
        self.isKeyPressed = False
        self.active_keys = {}
        
        try:
            initial_keys = g_configParams.eloHotKey.value
            if initial_keys and all(key > 0 for key in initial_keys):
                self.hot_keys = initial_keys
            else:
                print_debug("[MultiTextPanel] Invalid hot keys in config: %s, using default Alt" % str(initial_keys))
                self.hot_keys = [Keys.KEY_LALT]
            print_debug("[MultiTextPanel] Hot keys loaded: %s" % str(self.hot_keys))
        except Exception as e:
            print_error("[MultiTextPanel] Error loading hot keys: %s" % str(e))
            self.hot_keys = [Keys.KEY_LALT] 

        try:
            if not g_guiCache.isComponent('eloInfoPanel'): 
                print_debug("[MultiTextPanel] Creating main panel component...")
                position = g_configParams.panelPosition.value
                
                g_guiFlash.createComponent('eloInfoPanel', COMPONENT_TYPE.PANEL, {
                    'x': position[0],
                    'y': position[1],
                    'width': 150,
                    'height': 120,
                    'drag': True,
                    'border': False,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'visible': True
                })
                print_debug("[MultiTextPanel] Main panel created successfully")
            else:
                print_debug("[MultiTextPanel] Main panel already exists")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating main panel: %s" % str(e))
        
        print_debug("[MultiTextPanel] Initialization complete")

    def update_hotkeys(self):
        try:
            old_keys = self.hot_keys
            new_keys = g_configParams.eloHotKey.value
            
            if new_keys and all(key > 0 for key in new_keys):
                self.hot_keys = new_keys
                if old_keys != self.hot_keys:
                    print_debug("[MultiTextPanel] Hot keys updated: %s -> %s" % (str(old_keys), str(self.hot_keys)))
            else:
                print_debug("[MultiTextPanel] Invalid new keys: %s, keeping old: %s" % (str(new_keys), str(old_keys)))
        except Exception as e:
            print_error("[MultiTextPanel] Error updating hot keys: %s" % str(e))

    def create_text_fields(self, isVisible, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count):
        try:
            print_debug("[MultiTextPanel] Creating text fields with visibility: %s" % isVisible)
            
            current_y = 5
            
            # Перевіряємо налаштування видимості заголовка
            if g_configParams.showTitleVisible.value:
                header_component_id = 'eloInfoPanel.headerText'
                header_color = g_configParams.headerColor.getHexColor()
                header_text = '<font face="Tahoma" size="14" color="{0}"><b>-=Elo=-</b></font>'.format(header_color)
                
                g_guiFlash.createComponent(header_component_id, COMPONENT_TYPE.LABEL, {
                    'text': header_text,
                    'x': 10,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.CENTER,
                    'isHtml': True,
                    'visible': isVisible,
                    'shadow': self._getShadowConfig()
                })
                current_y += 20
            
            # Заміна showPlayerNames на showTeamNames
            if g_configParams.showTeamNames.value:
                names_component_id = 'eloInfoPanel.namesText'
                allies_name_color = g_configParams.alliesNamesColor.getHexColor()
                enemies_name_color = g_configParams.enemiesNamesColor.getHexColor()
                
                allies_short = (allies[:5].upper() if allies else "N/A")
                enemies_short = (enemies[:5].upper() if enemies else "N/A")
                
                names_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font><font face="Tahoma" size="18" color="{2}"><b>  {3}</b></font>'.format(
                    allies_name_color, allies_short, enemies_name_color, enemies_short
                )
                
                g_guiFlash.createComponent(names_component_id, COMPONENT_TYPE.LABEL, {
                    'text': names_text,
                    'x': 5,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'isHtml': True,
                    'visible': isVisible,
                    'shadow': self._getShadowConfig()
                })
                current_y += 20
            
            ratings_component_id = 'eloInfoPanel.ratingsText'
            allies_rating_color = g_configParams.alliesRatingColor.getHexColor()
            enemies_rating_color = g_configParams.enemiesRatingColor.getHexColor()
            
            allies_rating_str = str(allies_rating).zfill(4) if allies_rating else "0000"
            enemies_rating_str = str(enemies_rating).zfill(4) if enemies_rating else "0000"
            
            ratings_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font><font face="Tahoma" size="18" color="{2}"><b>      {3}</b></font>'.format(
                allies_rating_color, allies_rating_str, enemies_rating_color, enemies_rating_str
            )
            
            g_guiFlash.createComponent(ratings_component_id, COMPONENT_TYPE.LABEL, {
                'text': ratings_text,
                'x': 5,
                'y': current_y,
                'alignX': COMPONENT_ALIGN.CENTER,
                'isHtml': True,
                'visible': isVisible,
                'shadow': self._getShadowConfig()
            })
            current_y += 21
            
            if g_configParams.showEloChanges.value:
                elo_component_id = 'eloInfoPanel.eloText'
                elo_gain_color = g_configParams.eloGainColor.getHexColor()
                elo_loss_color = g_configParams.eloLossColor.getHexColor()
                
                elo_plus_str = "+{}".format(eloPlus) if eloPlus else "+0"
                elo_minus_str = "-{}".format(abs(eloMinus)) if eloMinus else "-0"
                
                elo_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font><font face="Tahoma" size="14" color="{2}"><b>          {3}</b></font>'.format(
                    elo_gain_color, elo_plus_str, elo_loss_color, elo_minus_str
                )
                
                g_guiFlash.createComponent(elo_component_id, COMPONENT_TYPE.LABEL, {
                    'text': elo_text,
                    'x': 5,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.CENTER,
                    'isHtml': True,
                    'visible': isVisible,
                    'shadow': self._getShadowConfig()
                })
                current_y += 17
            
            if g_configParams.showWinrateAndBattles.value:
                stats_component_id = 'eloInfoPanel.statsText'
                winrate_color = g_configParams.winrateColor.getHexColor()
                battles_color = g_configParams.battlesColor.getHexColor()
                
                winrate_str = "{}%".format(wins_percent) if wins_percent else "0%"
                battles_str = str(battles_count) if battles_count else "0"
                
                stats_text ='<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font><font face="Tahoma" size="14" color="{2}"><b>({3})</b></font>'.format(
                     battles_color, battles_str, winrate_color, winrate_str
                )
                
                g_guiFlash.createComponent(stats_component_id, COMPONENT_TYPE.LABEL, {
                    'text': stats_text,
                    'x': 5,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.CENTER,
                    'isHtml': True,
                    'visible': isVisible,
                    'shadow': self._getShadowConfig()
                })
            
            # Розрахунок видимих елементів
            visible_elements = 1  # Рейтинги завжди видимі
            if g_configParams.showTitleVisible.value:
                visible_elements += 1
            if g_configParams.showTeamNames.value:
                visible_elements += 1
            if g_configParams.showEloChanges.value:
                visible_elements += 1
            if g_configParams.showWinrateAndBattles.value:
                visible_elements += 1
                
            panel_height = 20 + (visible_elements * 25)
            g_guiFlash.updateComponent('eloInfoPanel', {'height': panel_height})
            
            print_debug("[MultiTextPanel] Text fields created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating text fields: %s" % str(e))

    def update_text_fields(self, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count):
        try:
            print_debug("[MultiTextPanel] Updating text fields")
            
            # Оновлення заголовка (якщо видимий)
            if g_configParams.showTitleVisible.value:
                header_component_id = 'eloInfoPanel.headerText'
                header_color = g_configParams.headerColor.getHexColor()
                header_text = '<font face="Tahoma" size="14" color="{0}"><b>-=Elo=-</b></font>'.format(header_color)
                
                if g_guiCache.isComponent(header_component_id):
                    g_guiFlash.updateComponent(header_component_id, {
                        'text': header_text,
                        'shadow': self._getShadowConfig()
                    })
            
            # Заміна showPlayerNames на showTeamNames
            if g_configParams.showTeamNames.value:
                names_component_id = 'eloInfoPanel.namesText'
                allies_name_color = g_configParams.alliesNamesColor.getHexColor()
                enemies_name_color = g_configParams.enemiesNamesColor.getHexColor()
                
                allies_short = (allies[:5].upper() if allies else "N/A")
                enemies_short = (enemies[:5].upper() if enemies else "N/A")
                
                names_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font><font face="Tahoma" size="18" color="{2}"><b>  {3}</b></font>'.format(
                    allies_name_color, allies_short, enemies_name_color, enemies_short
                )
                
                if g_guiCache.isComponent(names_component_id):
                    g_guiFlash.updateComponent(names_component_id, {
                        'text': names_text,
                        'shadow': self._getShadowConfig()
                    })

            ratings_component_id = 'eloInfoPanel.ratingsText'
            allies_rating_color = g_configParams.alliesRatingColor.getHexColor()
            enemies_rating_color = g_configParams.enemiesRatingColor.getHexColor()
            
            allies_rating_str = str(allies_rating).zfill(4) if allies_rating else "0000"
            enemies_rating_str = str(enemies_rating).zfill(4) if enemies_rating else "0000"
            
            ratings_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font><font face="Tahoma" size="18" color="{2}"><b>      {3}</b></font>'.format(
                allies_rating_color, allies_rating_str, enemies_rating_color, enemies_rating_str
            )
            
            if g_guiCache.isComponent(ratings_component_id):
                g_guiFlash.updateComponent(ratings_component_id, {
                    'text': ratings_text,
                    'shadow': self._getShadowConfig()
                })
            
            if g_configParams.showEloChanges.value:
                elo_component_id = 'eloInfoPanel.eloText'
                elo_gain_color = g_configParams.eloGainColor.getHexColor()
                elo_loss_color = g_configParams.eloLossColor.getHexColor()
                
                elo_plus_str = "+{}".format(eloPlus) if eloPlus else "+0"
                elo_minus_str = "-{}".format(abs(eloMinus)) if eloMinus else "-0"
                
                elo_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font><font face="Tahoma" size="14" color="{2}"><b>          {3}</b></font>'.format(
                    elo_gain_color, elo_plus_str, elo_loss_color, elo_minus_str
                )
                
                if g_guiCache.isComponent(elo_component_id):
                    g_guiFlash.updateComponent(elo_component_id, {
                        'text': elo_text,
                        'shadow': self._getShadowConfig()
                    })
            
            if g_configParams.showWinrateAndBattles.value:
                stats_component_id = 'eloInfoPanel.statsText'
                winrate_color = g_configParams.winrateColor.getHexColor()
                battles_color = g_configParams.battlesColor.getHexColor()
                
                winrate_str = "{}%".format(wins_percent) if wins_percent else "0%"
                battles_str = str(battles_count) if battles_count else "0"
                
                stats_text ='<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font><font face="Tahoma" size="14" color="{2}"><b> ({3})</b></font>'.format(
                    battles_color, battles_str, winrate_color, winrate_str
                )
                
                if g_guiCache.isComponent(stats_component_id):
                    g_guiFlash.updateComponent(stats_component_id, {
                        'text': stats_text,
                        'shadow': self._getShadowConfig()
                    })
            
            # Розрахунок видимих елементів
            visible_elements = 1  # Рейтинги завжди видимі
            if g_configParams.showTitleVisible.value:
                visible_elements += 1
            if g_configParams.showTeamNames.value:
                visible_elements += 1
            if g_configParams.showEloChanges.value:
                visible_elements += 1
            if g_configParams.showWinrateAndBattles.value:
                visible_elements += 1
                
            panel_height = 20 + (visible_elements * 25)
            if g_guiCache.isComponent('eloInfoPanel'):
                g_guiFlash.updateComponent('eloInfoPanel', {'height': panel_height})
            
            print_debug("[MultiTextPanel] Text fields updated successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error updating text fields: %s" % str(e))

    def _getShadowConfig(self):
        try:
            if not g_configParams.textShadowEnabled.value:
                return None
                
            shadow_color = g_configParams.textShadowColor.value
            shadow_color_int = (shadow_color[0] << 16) | (shadow_color[1] << 8) | shadow_color[2]
            
            # Обробка параметрів тіні (можуть бути списками)
            distance_val = g_configParams.textShadowDistance.value
            distance = distance_val[0] if isinstance(distance_val, list) and len(distance_val) > 0 else distance_val
            
            alpha_val = g_configParams.textShadowAlpha.value
            alpha = alpha_val[0] if isinstance(alpha_val, list) and len(alpha_val) > 0 else alpha_val
            
            blur_val = g_configParams.textShadowBlur.value
            blur = blur_val[0] if isinstance(blur_val, list) and len(blur_val) > 0 else blur_val
            
            return {
                'distance': distance,
                'angle': 45,
                'color': shadow_color_int,
                'alpha': alpha,
                'blurX': blur,
                'blurY': blur,
                'strength': 1,
                'quality': 1
            }
        except Exception as e:
            print_error("[MultiTextPanel] Error creating shadow config: %s" % str(e))
            return None

    def start_key_held(self, isVisible):
        try:
            print_debug("[MultiTextPanel] Setting visibility: %s" % isVisible)
            self.set_component_visibility(isVisible)
            if not isVisible:
                InputHandler.g_instance.onKeyDown += self._onKeyDown
                InputHandler.g_instance.onKeyUp += self._onKeyUp
                print_debug("[MultiTextPanel] Key handlers registered")
        except Exception as e:
            print_error("[MultiTextPanel] Error starting key held: %s" % str(e))

    def stop_key_held(self, is_always_visible):
        try:
            if not is_always_visible:
                InputHandler.g_instance.onKeyDown -= self._onKeyDown
                InputHandler.g_instance.onKeyUp -= self._onKeyUp
                print_debug("[MultiTextPanel] Key handlers unregistered")
        except Exception as e:
            print_error("[MultiTextPanel] Error stopping key held: %s" % str(e))

    def _onKeyDown(self, event):
        try:
            for key in self.hot_keys:
                if event.key == key and not self.active_keys.get(key, False):
                    self.active_keys[key] = True
                    print_debug("[MultiTextPanel] Key down: %s" % getBigworldNameFromKey(key))
                    break
            
            if self._allKeysPressed():
                if not self.isKeyPressed:
                    self.isKeyPressed = True
                    self.set_component_visibility(True)
                    print_debug("[MultiTextPanel] All keys pressed, showing components")
        except Exception as e:
            print_error("[MultiTextPanel] Error in _onKeyDown: %s" % str(e))

    def _onKeyUp(self, event):
        try:
            for key in self.hot_keys:
                if event.key == key and self.active_keys.get(key, False):
                    self.active_keys[key] = False
                    print_debug("[MultiTextPanel] Key up: %s" % getBigworldNameFromKey(key))
                    break
            
            if not self._allKeysPressed():
                if self.isKeyPressed:
                    self.isKeyPressed = False
                    self.set_component_visibility(False)
                    print_debug("[MultiTextPanel] Not all keys pressed, hiding components")
        except Exception as e:
            print_error("[MultiTextPanel] Error in _onKeyUp: %s" % str(e))

    def _allKeysPressed(self):
        return all(self.active_keys.get(key, False) for key in self.hot_keys)

    def set_component_visibility(self, visible):
        try:
            component_ids = ['eloInfoPanel.ratingsText']  # Рейтинги завжди в списку
            
            if g_configParams.showTitleVisible.value:
                component_ids.append('eloInfoPanel.headerText')
            if g_configParams.showTeamNames.value:
                component_ids.append('eloInfoPanel.namesText')
            if g_configParams.showEloChanges.value:
                component_ids.append('eloInfoPanel.eloText')
            if g_configParams.showWinrateAndBattles.value:
                component_ids.append('eloInfoPanel.statsText')
            
            for component_id in component_ids:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.updateComponent(component_id, {'visible': visible})
            
            print_debug("[MultiTextPanel] Component visibility set to: %s" % visible)
        except Exception as e:
            print_error("[MultiTextPanel] Error setting component visibility: %s" % str(e))

    def delete_all_component(self):
        try:
            component_ids = [
                'eloInfoPanel.headerText',
                'eloInfoPanel.namesText',
                'eloInfoPanel.ratingsText',
                'eloInfoPanel.eloText',
                'eloInfoPanel.statsText',
                'eloInfoPanel'
            ]
            
            for component_id in component_ids:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.deleteComponent(component_id)
                    print_debug("[MultiTextPanel] Deleted component: %s" % component_id)
            
            print_debug("[MultiTextPanel] All components deleted successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error deleting components: %s" % str(e))

    def update_panel_position(self, x, y):
        try:
            g_configParams.panelPosition.value = [x, y]
            if g_guiCache.isComponent('eloInfoPanel'):
                g_guiFlash.updateComponent('eloInfoPanel', {'x': x, 'y': y})
                print_debug("[MultiTextPanel] Panel position updated to: %s, %s" % (x, y))
        except Exception as e:
            print_error("[MultiTextPanel] Error updating panel position: %s" % str(e))

    def refresh_colors_and_effects(self):
        try:
            print_debug("[MultiTextPanel] Refreshing colors and effects")
            
            shadow_config = self._getShadowConfig()
            component_ids = [
                'eloInfoPanel.headerText',
                'eloInfoPanel.namesText',
                'eloInfoPanel.ratingsText',
                'eloInfoPanel.eloText',
                'eloInfoPanel.statsText'
            ]
            
            for component_id in component_ids:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.updateComponent(component_id, {'shadow': shadow_config})
            
            print_debug("[MultiTextPanel] Colors and effects refreshed successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error refreshing colors and effects: %s" % str(e))

    def recreate_components_with_visibility_changes(self):
        try:
            print_debug("[MultiTextPanel] Recreating components due to visibility changes")
            
            component_ids = [
                'eloInfoPanel.headerText',
                'eloInfoPanel.namesText',
                'eloInfoPanel.ratingsText',
                'eloInfoPanel.eloText',
                'eloInfoPanel.statsText'
            ]
            
            for component_id in component_ids:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.deleteComponent(component_id)
            
            from . import g_arenaInfoProvider
            if g_arenaInfoProvider and g_arenaInfoProvider.team_info:
                print_debug("[MultiTextPanel] Recreating components with current team info")
                display_mode = g_configParams.displayMode.value
                is_visible = (display_mode == "always")
                
                self.create_text_fields(
                    is_visible,
                    g_arenaInfoProvider.team_info.get('allies'),
                    g_arenaInfoProvider.team_info.get('enemies'),
                    g_arenaInfoProvider.team_info.get('allies_rating'),
                    g_arenaInfoProvider.team_info.get('enemies_rating'),
                    g_arenaInfoProvider.team_info.get('elo_plus'),
                    g_arenaInfoProvider.team_info.get('elo_minus'),
                    g_arenaInfoProvider.team_info.get('wins_percent'),
                    g_arenaInfoProvider.team_info.get('battles_count')
                )
            
            print_debug("[MultiTextPanel] Component recreation completed")
        except Exception as e:
            print_error("[MultiTextPanel] Error recreating components: %s" % str(e))