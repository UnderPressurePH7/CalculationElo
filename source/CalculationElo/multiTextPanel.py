# -*- coding: utf-8 -*-
import BigWorld
import Keys
from gui import InputHandler
from gui.shared.utils.key_mapping import getBigworldNameFromKey

from gui.mods.gambiter import g_guiFlash, utils
from gui.mods.gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, g_guiCache, COMPONENT_EVENT

from .config_param import g_configParams
from .utils import print_error, print_debug

class MultiTextPanel:

    utils.IS_DEBUG = False

    def __init__(self):
        print_debug("[MultiTextPanel] Initializing...")
        self.isKeyPressed = False
        self.active_keys = {}
        self.components_created = False  
        
        self.currentPanelX = g_configParams.panelPosition.value[0]
        self.currentPanelY = g_configParams.panelPosition.value[1]
        self.wasPositionEdited = False

        self._save_callback_id = None
        
        COMPONENT_EVENT.UPDATED += self._onComponentUpdated
        
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

        self._ensure_main_panel()
        
        print_debug("[MultiTextPanel] Initialization complete")

    def _ensure_main_panel(self):
        try:
            if not g_guiCache.isComponent('eloInfoPanel'): 
                print_debug("[MultiTextPanel] Creating main panel component...")
                
                g_guiFlash.createComponent('eloInfoPanel', COMPONENT_TYPE.PANEL, {
                    'x': self.currentPanelX,
                    'y': self.currentPanelY,
                    'width': 165,
                    'height': 120,
                    'drag': True, 
                    'limit': True,  
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

    def _onComponentUpdated(self, alias, props):
        try:
            if alias != 'eloInfoPanel':
                return
                
            new_x = props.get('x')
            new_y = props.get('y')
            
            if new_x is not None and new_y is not None:
                if new_x != self.currentPanelX or new_y != self.currentPanelY:
                    print_debug("[MultiTextPanel] Panel position changed: [%d, %d] -> [%d, %d]" % 
                               (self.currentPanelX, self.currentPanelY, new_x, new_y))
                    
                    new_x = max(0, min(new_x, 1920 - 165)) 
                    new_y = max(0, min(new_y, 1080 - 120))  
                    
                    self.currentPanelX = new_x
                    self.currentPanelY = new_y
                    self.wasPositionEdited = True

                    self._schedule_position_save()
                    
                    print_debug("[MultiTextPanel] Panel position updated")
        except Exception as e:
            print_error("[MultiTextPanel] Error in component update handler: %s" % str(e))

    def persistParamsIfChanged(self):
        if self.wasPositionEdited:
            try:
                from .config import g_config
                from .config_param import g_configParams
                
                g_configParams.panelPosition.value = [self.currentPanelX, self.currentPanelY]
                
                g_config.save_config()
                self.wasPositionEdited = False
                print_debug("[MultiTextPanel] Panel position saved: [%d, %d]" % (self.currentPanelX, self.currentPanelY))
            except Exception as e:
                print_error("[MultiTextPanel] Error saving panel position: %s" % str(e))

    def _getShadowConfig(self):
        try:
            if g_configParams.textShadowEnabled.value:
                shadow_color = g_configParams.textShadowColor.value
                shadow_distance = g_configParams.textShadowDistance.value[0] if g_configParams.textShadowDistance.value else 1
                shadow_alpha = g_configParams.textShadowAlpha.value[0] if g_configParams.textShadowAlpha.value else 0.5
                shadow_blur = g_configParams.textShadowBlur.value[0] if g_configParams.textShadowBlur.value else 2
                
                shadow_color_hex = (shadow_color[0] << 16) | (shadow_color[1] << 8) | shadow_color[2]
                
                return {
                    'distance': shadow_distance,
                    'angle': 45,
                    'color': shadow_color_hex,
                    'alpha': shadow_alpha,
                    'blurX': shadow_blur,
                    'blurY': shadow_blur,
                    'strength': 1,
                    'quality': 1
                }
            else:
                return None
        except Exception as e:
            print_error("[MultiTextPanel] Error getting shadow config: %s" % str(e))
            return {
                'distance': 1,
                'angle': 45,
                'color': 0x000000,
                'alpha': 0.5,
                'blurX': 2,
                'blurY': 2,
                'strength': 1,
                'quality': 1
            }

    def create_text_fields(self, isVisible, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count, avg_team_wn8):
        try:
            print_debug("[MultiTextPanel] Creating text fields with visibility: %s" % isVisible)
            
            self._ensure_main_panel()

            if not self.components_created:
                print_debug("[MultiTextPanel] Creating components for the first time")
                
                current_y = 5
                shadow_config = self._getShadowConfig()
                
                if g_configParams.showTitleVisible.value:
                    header_color = g_configParams.headerColor.getHexColor()
                    header_text = '<font face="Tahoma" size="14" color="{0}"><b>-=Calculation Elo=-</b></font>'.format(header_color)
                    
                    component_props = {
                        'text': header_text,
                        'x': 0,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.CENTER,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        component_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.headerText', COMPONENT_TYPE.LABEL, component_props)
                    current_y += 20

                if g_configParams.showTeamNames.value:
                    allies_color = g_configParams.alliesNamesColor.getHexColor()
                    enemies_color = g_configParams.enemiesNamesColor.getHexColor()

                    allies_props = {
                        'text': '<font face="Tahoma" size="18" color="{0}"><b>ALLY</b></font>'.format(allies_color),
                        'x': 1,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.LEFT,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        allies_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.alliesNameText', COMPONENT_TYPE.LABEL, allies_props)

                    enemies_props = {
                        'text': '<font face="Tahoma" size="18" color="{0}"><b>ENEM</b></font>'.format(enemies_color),
                        'x': -1,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.RIGHT,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        enemies_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.enemiesNameText', COMPONENT_TYPE.LABEL, enemies_props)
                    current_y += 20

                # Рейтинги команд
                allies_rating_color = g_configParams.alliesRatingColor.getHexColor()
                enemies_rating_color = g_configParams.enemiesRatingColor.getHexColor()

                allies_rating_props = {
                    'text': '<font face="Tahoma" size="18" color="{0}"><b>0000</b></font>'.format(allies_rating_color),
                    'x': 15,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'isHtml': True,
                    'visible': isVisible
                }
                if shadow_config:
                    allies_rating_props['shadow'] = shadow_config
                
                g_guiFlash.createComponent('eloInfoPanel.alliesRatingText', COMPONENT_TYPE.LABEL, allies_rating_props)

                enemies_rating_props = {
                    'text': '<font face="Tahoma" size="18" color="{0}"><b>0000</b></font>'.format(enemies_rating_color),
                    'x': -15,
                    'y': current_y,
                    'alignX': COMPONENT_ALIGN.RIGHT,
                    'isHtml': True,
                    'visible': isVisible
                }
                if shadow_config:
                    enemies_rating_props['shadow'] = shadow_config
                
                g_guiFlash.createComponent('eloInfoPanel.enemiesRatingText', COMPONENT_TYPE.LABEL, enemies_rating_props)
                current_y += 21

                if g_configParams.showEloChanges.value:
                    elo_gain_color = g_configParams.eloGainColor.getHexColor()
                    elo_loss_color = g_configParams.eloLossColor.getHexColor()

                    elo_plus_props = {
                        'text': '<font face="Tahoma" size="14" color="{0}"><b>+0</b></font>'.format(elo_gain_color),
                        'x': 30,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.LEFT,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        elo_plus_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.eloPlusText', COMPONENT_TYPE.LABEL, elo_plus_props)

                    elo_minus_props = {
                        'text': '<font face="Tahoma" size="14" color="{0}"><b>-0</b></font>'.format(elo_loss_color),
                        'x': -30,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.RIGHT,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        elo_minus_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.eloMinusText', COMPONENT_TYPE.LABEL, elo_minus_props)
                    current_y += 17

                if g_configParams.showWinrateAndBattles.value:
                    winrate_color = g_configParams.winrateColor.getHexColor()
                    battles_color = g_configParams.battlesColor.getHexColor()
                    stats_text = '<font face="Tahoma" size="14" color="{0}"><b>0</b></font> <font face="Tahoma" size="14" color="{1}"><b>(0%)</b></font>'.format(battles_color, winrate_color)
                    
                    stats_props = {
                        'text': stats_text,
                        'x': 0,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.CENTER,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        stats_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.statsText', COMPONENT_TYPE.LABEL, stats_props)
                    current_y += 17

                if g_configParams.showAvgTeamWn8.value:
                    avg_wn8_color = g_configParams.avgWN8Color.getHexColor()

                    avg_wn8_props = {
                        'text': '<font face="Tahoma" size="14" color="{0}"><b>wn8 0</b></font>'.format(avg_wn8_color),
                        'x': 0,
                        'y': current_y,
                        'alignX': COMPONENT_ALIGN.CENTER,
                        'isHtml': True,
                        'visible': isVisible
                    }
                    if shadow_config:
                        avg_wn8_props['shadow'] = shadow_config
                    
                    g_guiFlash.createComponent('eloInfoPanel.avgTeamWn8Text', COMPONENT_TYPE.LABEL, avg_wn8_props)

                self.components_created = True
                print_debug("[MultiTextPanel] All components created successfully")
            self.update_text_fields(allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count, avg_team_wn8)

        except Exception as e:
            print_error("[MultiTextPanel] Error creating text fields: %s" % str(e))

    def update_text_fields(self, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count, avg_team_wn8):
        try:
            print_debug("[MultiTextPanel] Updating text fields")
            
            if not self.components_created:
                print_debug("[MultiTextPanel] Components not created yet, skipping update")
                return

            shadow_config = self._getShadowConfig()
            
            if g_configParams.showTitleVisible.value and g_guiCache.isComponent('eloInfoPanel.headerText'):
                header_color = g_configParams.headerColor.getHexColor()
                header_text = '<font face="Tahoma" size="14" color="{0}"><b>-=Calculation Elo=-</b></font>'.format(header_color)
                
                update_props = {'text': header_text}
                if shadow_config:
                    update_props['shadow'] = shadow_config
                
                g_guiFlash.updateComponent('eloInfoPanel.headerText', update_props)

            if g_configParams.showTeamNames.value:
                allies_color = g_configParams.alliesNamesColor.getHexColor()
                enemies_color = g_configParams.enemiesNamesColor.getHexColor()

                allies_short = (allies[:4].upper() if allies else "ALLY")
                if g_guiCache.isComponent('eloInfoPanel.alliesNameText'):
                    allies_name_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(allies_color, allies_short)
                    
                    update_props = {'text': allies_name_text}
                    if shadow_config:
                        update_props['shadow'] = shadow_config
                    
                    g_guiFlash.updateComponent('eloInfoPanel.alliesNameText', update_props)

                enemies_short = (enemies[:4].upper() if enemies else "ENEM")
                if g_guiCache.isComponent('eloInfoPanel.enemiesNameText'):
                    enemies_name_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(enemies_color, enemies_short)
                    
                    update_props = {'text': enemies_name_text}
                    if shadow_config:
                        update_props['shadow'] = shadow_config
                    
                    g_guiFlash.updateComponent('eloInfoPanel.enemiesNameText', update_props)

            allies_rating_color = g_configParams.alliesRatingColor.getHexColor()
            enemies_rating_color = g_configParams.enemiesRatingColor.getHexColor()

            allies_rating_str = str(allies_rating).zfill(4) if allies_rating else "0000"
            if g_guiCache.isComponent('eloInfoPanel.alliesRatingText'):
                allies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(allies_rating_color, allies_rating_str)
                
                update_props = {'text': allies_rating_text}
                if shadow_config:
                    update_props['shadow'] = shadow_config
                
                g_guiFlash.updateComponent('eloInfoPanel.alliesRatingText', update_props)

            enemies_rating_str = str(enemies_rating).zfill(4) if enemies_rating else "0000"
            if g_guiCache.isComponent('eloInfoPanel.enemiesRatingText'):
                enemies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(enemies_rating_color, enemies_rating_str)
                
                update_props = {'text': enemies_rating_text}
                if shadow_config:
                    update_props['shadow'] = shadow_config
                
                g_guiFlash.updateComponent('eloInfoPanel.enemiesRatingText', update_props)

            if g_configParams.showEloChanges.value:
                elo_gain_color = g_configParams.eloGainColor.getHexColor()
                elo_loss_color = g_configParams.eloLossColor.getHexColor()

                elo_plus_str = "+{}".format(eloPlus) if eloPlus else "+0"
                if g_guiCache.isComponent('eloInfoPanel.eloPlusText'):
                    elo_plus_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font>'.format(elo_gain_color, elo_plus_str)
                    
                    update_props = {'text': elo_plus_text}
                    if shadow_config:
                        update_props['shadow'] = shadow_config
                    
                    g_guiFlash.updateComponent('eloInfoPanel.eloPlusText', update_props)

                elo_minus_str = "{}".format(eloMinus) if eloMinus else "-0"
                if g_guiCache.isComponent('eloInfoPanel.eloMinusText'):
                    elo_minus_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font>'.format(elo_loss_color, elo_minus_str)
                    
                    update_props = {'text': elo_minus_text}
                    if shadow_config:
                        update_props['shadow'] = shadow_config
                    
                    g_guiFlash.updateComponent('eloInfoPanel.eloMinusText', update_props)

            if g_configParams.showWinrateAndBattles.value and g_guiCache.isComponent('eloInfoPanel.statsText'):
                winrate_color = g_configParams.winrateColor.getHexColor()
                battles_color = g_configParams.battlesColor.getHexColor()

                battles_str = str(battles_count) if battles_count else "0"
                winrate_str = "{}%".format(wins_percent) if wins_percent else "0%"
                stats_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font> <font face="Tahoma" size="14" color="{2}"><b>({3})</b></font>'.format(
                    battles_color, battles_str, winrate_color, winrate_str)
                
                update_props = {'text': stats_text}
                if shadow_config:
                    update_props['shadow'] = shadow_config
                
                g_guiFlash.updateComponent('eloInfoPanel.statsText', update_props)
                
            if g_configParams.showAvgTeamWn8.value and g_guiCache.isComponent('eloInfoPanel.avgTeamWn8Text'):
                avg_wn8_color = g_configParams.avgWN8Color.getHexColor()
                avg_team_wn8_str = str(avg_team_wn8).zfill(4) if avg_team_wn8 else "0000"
                
                avg_wn8_text = '<font face="Tahoma" size="14" color="{0}"><b>wn8 {1}</b></font>'.format(avg_wn8_color, avg_team_wn8_str)
                
                update_props = {'text': avg_wn8_text}
                if shadow_config:
                    update_props['shadow'] = shadow_config
                
                g_guiFlash.updateComponent('eloInfoPanel.avgTeamWn8Text', update_props)

            print_debug("[MultiTextPanel] Text fields updated successfully")
            
        except Exception as e:
            print_error("[MultiTextPanel] Error updating text fields: %s" % str(e))

    def start_key_held(self, elo_visible):
        try:
            print_debug("[MultiTextPanel] Setting visibility: %s" % elo_visible)
            self.set_component_visibility(elo_visible)
            if not elo_visible:
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
                    break
            
            if all(self.active_keys.get(key, False) for key in self.hot_keys):
                if not self.isKeyPressed:
                    self.isKeyPressed = True
                    self.set_component_visibility(True)
                    print_debug("[MultiTextPanel] All hotkeys pressed, showing panel")
        except Exception as e:
            print_error("[MultiTextPanel] Error in key down handler: %s" % str(e))

    def _onKeyUp(self, event):
        try:
            for key in self.hot_keys:
                if event.key == key and self.active_keys.get(key, False):
                    self.active_keys[key] = False
                    break
            
            if not any(self.active_keys.get(key, False) for key in self.hot_keys):
                if self.isKeyPressed:
                    self.isKeyPressed = False
                    self.set_component_visibility(False)
                    print_debug("[MultiTextPanel] All hotkeys released, hiding panel")
        except Exception as e:
            print_error("[MultiTextPanel] Error in key up handler: %s" % str(e))

    def set_component_visibility(self, isVisible):
        try:
            print_debug("[MultiTextPanel] Setting component visibility: %s" % isVisible)
            
            component_ids = [
                'eloInfoPanel.headerText',
                'eloInfoPanel.alliesNameText',
                'eloInfoPanel.enemiesNameText', 
                'eloInfoPanel.alliesRatingText',
                'eloInfoPanel.enemiesRatingText',
                'eloInfoPanel.eloPlusText',
                'eloInfoPanel.eloMinusText',
                'eloInfoPanel.statsText',
                'eloInfoPanel.avgTeamWn8Text'
            ]
            
            for component_id in component_ids:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.updateComponent(component_id, {'visible': isVisible})
            
            print_debug("[MultiTextPanel] Component visibility updated successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error setting component visibility: %s" % str(e))

    def delete_all_component(self):
        try:
            self.persistParamsIfChanged()
            print_debug("[MultiTextPanel] Soft cleanup - keeping components but hiding them")
            self.set_component_visibility(False)
            
            print_debug("[MultiTextPanel] Soft cleanup completed")
        except Exception as e:
            print_error("[MultiTextPanel] Error in soft cleanup: %s" % str(e))

    def force_cleanup(self):
        try:
            print_debug("[MultiTextPanel] Starting FULL cleanup...")
            
            try:
                InputHandler.g_instance.onKeyDown -= self._onKeyDown
                InputHandler.g_instance.onKeyUp -= self._onKeyUp
                print_debug("[MultiTextPanel] Key handlers force unregistered")
            except Exception as e:
                print_debug("[MultiTextPanel] Key handlers already unregistered: %s" % str(e))
            
            self.persistParamsIfChanged()
            
            try:
                COMPONENT_EVENT.UPDATED -= self._onComponentUpdated
                print_debug("[MultiTextPanel] Component event handlers unregistered")
            except Exception as e:
                print_debug("[MultiTextPanel] Component event handlers already unregistered: %s" % str(e))

            self.isKeyPressed = False
            self.active_keys = {}
            self.components_created = False  
            
            component_ids = [
                'eloInfoPanel.headerText',
                'eloInfoPanel.alliesNameText',
                'eloInfoPanel.enemiesNameText', 
                'eloInfoPanel.alliesRatingText',
                'eloInfoPanel.enemiesRatingText',
                'eloInfoPanel.eloPlusText',
                'eloInfoPanel.eloMinusText',
                'eloInfoPanel.statsText',
                'eloInfoPanel.avgTeamWn8Text',
                'eloInfoPanel' 
            ]
            
            for component_id in component_ids:
                try:
                    if g_guiCache.isComponent(component_id):
                        g_guiFlash.deleteComponent(component_id)
                        print_debug("[MultiTextPanel] Force deleted component: %s" % component_id)
                except Exception as e:
                    print_debug("[MultiTextPanel] Could not delete component %s: %s" % (component_id, str(e)))
            
            print_debug("[MultiTextPanel] FULL cleanup completed")
            
        except Exception as e:
            print_error("[MultiTextPanel] Error in force cleanup: %s" % str(e))


    def _schedule_position_save(self):
        try:
            if hasattr(self, '_save_callback_id') and self._save_callback_id:
                BigWorld.cancelCallback(self._save_callback_id)
            self._save_callback_id = BigWorld.callback(2.0, self._delayed_position_save)
            print_debug("[MultiTextPanel] Position save scheduled")
        except Exception as e:
            print_error("[MultiTextPanel] Error scheduling position save: %s" % str(e))

    def _delayed_position_save(self):
        try:
            self._save_callback_id = None
            if self.wasPositionEdited:
                self.persistParamsIfChanged()
                print_debug("[MultiTextPanel] Delayed position save completed")
        except Exception as e:
            print_error("[MultiTextPanel] Error in delayed position save: %s" % str(e))