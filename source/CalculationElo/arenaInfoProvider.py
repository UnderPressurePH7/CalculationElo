# -*- coding: utf-8 -*-
import BigWorld
from PlayerEvents import g_playerEvents
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from .config import g_config
from .config_param import g_configParams

from . import *

from .utils import *


class ArenaInfoProvider():
    __playerTeam = -1
    __guiType = -1
    __tank_tier = 10
    __arena = None

    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        print_debug("[ArenaInfoProvider] Initializing...")
        self.account_ids = []
        self.ON_HOTKEY_PRESSED = False

        try:
            print_debug("[ArenaInfoProvider] Creating text fields")
            g_multiTextPanel.create_text_fields(self.ON_HOTKEY_PRESSED)

        except Exception as ex:
            print_error("[ArenaInfoProvider] Error creating text fields: %s" % str(ex))

        try:
            g_playerEvents.onAvatarReady += self.start
            g_playerEvents.onAvatarBecomeNonPlayer += self.stop
            self.sessionProvider.onBattleSessionStart += self.onBattleSessionStart
            self.sessionProvider.onBattleSessionStop += self.onBattleSessionStop
            print_debug("[ArenaInfoProvider] Event handlers registered successfully")
        except Exception as e:
            print_error("[ArenaInfoProvider] Error registering event handlers: %s" % str(e))

        print_debug("[ArenaInfoProvider] Initialization complete")

    def start(self, *a, **k):
        print_debug("[ArenaInfoProvider] Starting...")
        
        self.account_ids = []

        def waitVehicles():
            try:
                print_debug("[ArenaInfoProvider] Waiting for vehicles...")
                
                display_mode = g_configParams.displayMode.value
                self.ON_HOTKEY_PRESSED = (display_mode == "always")
                print_debug("[ArenaInfoProvider] Display mode: %s, ON_HOTKEY_PRESSED: %s" % (display_mode, self.ON_HOTKEY_PRESSED))
                
                vehicles = BigWorld.player().arena.vehicles.items()
                if len(vehicles) == 0:
                    print_debug("[ArenaInfoProvider] No vehicles found, retrying...")
                    BigWorld.callback(0.1, waitVehicles)
                    return
                print_debug("[ArenaInfoProvider] Found %d vehicles" % len(vehicles))
                
                if g_configParams.enabled.value:
                    print_debug("[ArenaInfoProvider] Mod enabled, processing...")

                    
                    if self.__guiType in (15, 16):
                        print_debug("[ArenaInfoProvider] Valid GUI type: %d" % self.__guiType)

                        self.__playerTeam = BigWorld.player().team
                        print_debug("[ArenaInfoProvider] Player team: %d" % self.__playerTeam)

                        allies_name, enemies_name = self.get_team_names()
                        print_debug("[ArenaInfoProvider] Team info set - allies: %s, enemies: %s" % (allies_name, enemies_name))
                        
                        g_multiTextPanel.set_panel_visibility(True)
                        g_multiTextPanel.update_text_fields(allies_name, enemies_name, 0, 0, 0, 0, 0, 0 )
                        
                        async_state = {
                            'allies_name': allies_name,
                            'enemies_name': enemies_name,
                            'allies_clan_id': None,
                            'enemies_clan_id': None,
                            'allies_rating': None,
                            'enemies_rating': None,
                            'elo_plus': None,
                            'elo_minus': None,
                            'wins_percent': None,
                            'battles_count': None,
                            'avg_team_wn8': None,
                            'pending_operations': 0
                        }

                        self.__tank_tier = self.get_player_tank_tier(BigWorld.player().playerVehicleID)
                        print_debug("[ArenaInfoProvider] Player tank tier: %d" % self.__tank_tier)

                        def update_ui_if_ready():
                            if async_state['pending_operations'] <= 0:
                                print_debug("[ArenaInfoProvider] All async operations completed, updating UI")
                                g_multiTextPanel.update_text_fields(
                                    async_state['allies_name'], 
                                    async_state['enemies_name'], 
                                    async_state['allies_rating'] or 0, 
                                    async_state['enemies_rating'] or 0, 
                                    async_state['elo_plus'] or 0, 
                                    async_state['elo_minus'] or 0, 
                                    async_state['wins_percent'] or 0, 
                                    async_state['battles_count'] or 0
                                )

                        def allies_clan_id_callback(clan_tag, clan_id):
                            try:
                                print_debug("[ArenaInfoProvider] Received allies clan_id: %s" % clan_id)
                                async_state['allies_clan_id'] = clan_id
                                
                                if clan_id:
                                    async_state['pending_operations'] += 1
                                    g_clanAPI.get_clan_rating(clan_id, self.__tank_tier, self.__guiType, allies_rating_callback)
                                
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()
                            except Exception as e:
                                print_error("[ArenaInfoProvider] Error in allies_clan_id_callback: %s" % str(e))
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()

                        def allies_rating_callback(clan_id, battle_lvl, gui_type, rating):
                            try:
                                print_debug("[ArenaInfoProvider] Received allies rating: %s" % rating)
                                async_state['allies_rating'] = rating
                                
                                if async_state['enemies_rating'] is not None and g_configParams.showEloChanges.value:
                                    elo_changes = g_eloCalc.calculate_elo_changes(rating, async_state['enemies_rating'])
                                    async_state['elo_plus'] = elo_changes[0]
                                    async_state['elo_minus'] = elo_changes[1]
                                
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()
                            except Exception as e:
                                print_error("[ArenaInfoProvider] Error in allies_rating_callback: %s" % str(e))
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()

                        def enemies_clan_id_callback(clan_tag, clan_id):
                            try:
                                print_debug("[ArenaInfoProvider] Received enemies clan_id: %s" % clan_id)
                                async_state['enemies_clan_id'] = clan_id
                                
                                if clan_id:
                                    async_state['pending_operations'] += 1
                                    g_clanAPI.get_clan_rating(clan_id, self.__tank_tier, self.__guiType, enemies_rating_callback)
                                    
                                    if g_configParams.showWinrateAndBattles.value:
                                        async_state['pending_operations'] += 1
                                        g_clanAPI.get_for_last_28_days(clan_id, self.__tank_tier, self.__guiType, stats_28_days_callback)
                                
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()
                            except Exception as e:
                                print_error("[ArenaInfoProvider] Error in enemies_clan_id_callback: %s" % str(e))
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()

                        def enemies_rating_callback(clan_id, battle_lvl, gui_type, rating):
                            try:
                                print_debug("[ArenaInfoProvider] Received enemies rating: %s" % rating)
                                async_state['enemies_rating'] = rating
                                
                                if async_state['allies_rating'] is not None and g_configParams.showEloChanges.value:
                                    elo_changes = g_eloCalc.calculate_elo_changes(async_state['allies_rating'], rating)
                                    async_state['elo_plus'] = elo_changes[0]
                                    async_state['elo_minus'] = elo_changes[1]
                                
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()
                            except Exception as e:
                                print_error("[ArenaInfoProvider] Error in enemies_rating_callback: %s" % str(e))
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()

                        def stats_28_days_callback(clan_id, battle_lvl, gui_type, wins_percent, battles_count):
                            try:
                                print_debug("[ArenaInfoProvider] Received 28-day stats: %s%% wins, %s battles" % (wins_percent, battles_count))
                                async_state['wins_percent'] = wins_percent
                                async_state['battles_count'] = battles_count
                                
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()
                            except Exception as e:
                                print_error("[ArenaInfoProvider] Error in stats_28_days_callback: %s" % str(e))
                                async_state['pending_operations'] -= 1
                                update_ui_if_ready()

                        async_state['pending_operations'] += 2
                        
                        g_clanAPI.get_clan_id(async_state['allies_name'], allies_clan_id_callback)
                        g_clanAPI.get_clan_id(async_state['enemies_name'], enemies_clan_id_callback)

                        if g_configParams.showAvgTeamWn8.value or g_configParams.recordAvgTeamWn8.value:
                            self.set_account_ids_in_battle(vehicles)
                            print_debug("[ArenaInfoProvider] Account IDs in battle set: %s" % self.account_ids)
                            
                            def wn8_callback(avg_wn8):
                                try:
                                    print_debug("[ArenaInfoProvider] Received async WN8 result: %s" % avg_wn8)
                                    async_state['avg_team_wn8'] = avg_wn8
                                    
                                    g_avgWN8.save_team_wn8_history(avg_wn8, async_state['enemies_name'], async_state['enemies_rating'] or 0)

                                    if g_configParams.showAvgTeamWn8.value and avg_wn8 > 0:
                                        try:
                                            g_multiTextPanel.update_avg_wn8_display(avg_wn8)
                                            print_debug("[ArenaInfoProvider] WN8 display updated with async result")
                                        except Exception as e:
                                            print_error("[ArenaInfoProvider] Error updating WN8 display: %s" % str(e))
                                            
                                except Exception as e:
                                    print_error("[ArenaInfoProvider] Error in WN8 callback: %s" % str(e))

                            g_avgWN8.get_avg_team_wn8(self.account_ids, wn8_callback)

                    else:
                        g_multiTextPanel.set_panel_visibility(False)
                        print_debug("[ArenaInfoProvider] Invalid GUI type: %d" % self.__guiType)
                else:
                    print_debug("[ArenaInfoProvider] Mod disabled")
                    
            except Exception as e:
                print_error("[ArenaInfoProvider] Error in waitVehicles: %s" % str(e))
                
        waitVehicles()

    def stop(self, *a, **k):
        print_debug("[ArenaInfoProvider] Stopping...")

        try:
            g_avgWN8.clear_wn8_cache()
            g_clanAPI.clear_cache()
            g_multiTextPanel.persistParamsIfChanged() 
            g_multiTextPanel.delete_all_component() 
            print_debug("[ArenaInfoProvider] Components hidden successfully")
        except Exception as ex:
            print_error('[ArenaInfoProvider] Error hiding components: %s' % str(ex))

    def onBattleSessionStart(self):
        print_debug("[ArenaInfoProvider] Battle session started")

        try:
            arena = BigWorld.player().arena
            self.__guiType = BigWorld.player().arena.guiType
            print_debug("[ArenaInfoProvider] GUI type: %d" % self.__guiType)
            
            display_mode = g_configParams.displayMode.value
            self.ON_HOTKEY_PRESSED = (display_mode == "always")
            print_debug("[ArenaInfoProvider] Display mode: %s, always visible: %s" % (display_mode, self.ON_HOTKEY_PRESSED))
            
            g_multiTextPanel.start_key_held(self.ON_HOTKEY_PRESSED)
            
            g_config.sync_with_msa()
                
            self.__arena = arena
            
        except Exception as ex:
            print_error("[ArenaInfoProvider] Error in onBattleSessionStart: %s" % str(ex))

    def onBattleSessionStop(self):
        print_debug("[ArenaInfoProvider] Battle session stopped")
        
        try:
            arena = self.__arena
            
            g_multiTextPanel.stop_key_held(self.ON_HOTKEY_PRESSED)
            print_debug("[ArenaInfoProvider] Key handlers stopped")

            try:
                g_multiTextPanel.delete_all_component()
                print_debug("[ArenaInfoProvider] Components hidden in session stop")
            except Exception as e:
                print_error("[ArenaInfoProvider] Error hiding components in session stop: %s" % str(e))
            
            self.__arena = None
            print_debug("[ArenaInfoProvider] Arena reference cleared")
            
        except Exception as e:
            print_error("[ArenaInfoProvider] Error in onBattleSessionStop: %s" % str(e))

    def get_team_names(self):
        try:
            print_debug("[ArenaInfoProvider] Getting team names...")
            
            arena_dp = BigWorld.player().guiSessionProvider.getArenaDP()
            personal_description = arena_dp.getPersonalDescription()
            
            if self.__playerTeam == 2:
                allies = personal_description.getTeamName(2)
                enemies = personal_description.getTeamName(1)
                print_debug("[ArenaInfoProvider] Player on team 2 - allies: %s, enemies: %s" % (allies, enemies))
            else: 
                allies = personal_description.getTeamName(1)
                enemies = personal_description.getTeamName(2)
                print_debug("[ArenaInfoProvider] Player on team 1 - allies: %s, enemies: %s" % (allies, enemies))
                
            return allies, enemies
                
        except Exception as e:
            print_error("[ArenaInfoProvider] Error getting team names: %s" % str(e))
            return "Unknown", "Unknown"

    def set_account_ids_in_battle(self, vehicles_items):
        try:
            for vehicle_id, vehicle_info in vehicles_items:
                if vehicle_info['team'] != self.__playerTeam:
                    account_id = vehicle_info['accountDBID']
                    self.account_ids.append(account_id)
        except Exception as e:
            print_debug("[ArenaInfoProvider] Error setting acc_ids: %s" % str(e))
            self.account_ids = []

    def get_player_tank_tier(self, vehicle_id):
        try:
            print_debug("[ArenaInfoProvider] Getting tank tier for vehicle ID: %s" % vehicle_id)
            
            vehicles = BigWorld.player().arena.vehicles
            if vehicle_id in vehicles:
                tier = vehicles[vehicle_id]['vehicleType'].level
                print_debug("[ArenaInfoProvider] Tank tier found: %d" % tier)
                return tier
            else:
                print_debug("[ArenaInfoProvider] Vehicle ID not found, using default tier 10")
                return 10
                
        except Exception as e:
            print_error("[ArenaInfoProvider] Error getting tank tier: %s" % str(e))
            return 10
    
    def fini(self):       
        print_debug("[ArenaInfoProvider] Finalizing...")
        
        try:
            try:
                g_multiTextPanel.force_cleanup() 
                print_debug("[ArenaInfoProvider] Components FULLY cleaned up during finalization")
            except Exception as e:
                print_error("[ArenaInfoProvider] Error in force cleanup during fini: %s" % str(e))

            g_playerEvents.onAvatarReady -= self.start
            g_playerEvents.onAvatarBecomeNonPlayer -= self.stop
            self.sessionProvider.onBattleSessionStart -= self.onBattleSessionStart
            self.sessionProvider.onBattleSessionStop -= self.onBattleSessionStop
            print_debug("[ArenaInfoProvider] Event handlers unregistered successfully")
            
        except Exception as e:
            print_error("[ArenaInfoProvider] Error unregistering event handlers: %s" % str(e))
            
        print_debug("[ArenaInfoProvider] Finalization complete")