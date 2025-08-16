# -*- coding: utf-8 -*-
import BigWorld
from PlayerEvents import g_playerEvents
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from gui.mods.gambiter.flash import g_guiCache

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
        
        self.team_info = {'allies': None, 'enemies': None, 'id_allies': None, 'id_enemies': None, 
                          'allies_rating': None, 'enemies_rating': None, 
                          'elo_plus': None, 'elo_minus': None, 'wins_percent': None, 'battles_count': None }
        
        self.ON_HOTKEY_PRESSED = False

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
        
        self.team_info = {'allies': None, 'enemies': None, 'id_allies': None, 'id_enemies': None,
                      'allies_rating': None, 'enemies_rating': None,
                      'elo_plus': None, 'elo_minus': None, 'wins_percent': None, 'battles_count': None}
        
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

                        self.set_team_info()
                        print_debug("[ArenaInfoProvider] Team info set - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
                        
                        self.team_info['id_allies'] = g_clanAPI.get_clan_id(self.team_info['allies'])
                        self.team_info['id_enemies'] = g_clanAPI.get_clan_id(self.team_info['enemies'])
                        print_debug("[ArenaInfoProvider] Clan IDs - allies: %s, enemies: %s" % (self.team_info['id_allies'], self.team_info['id_enemies']))

                        self.__tank_tier = self.get_player_tank_tier(BigWorld.player().playerVehicleID)
                        print_debug("[ArenaInfoProvider] Player tank tier: %d" % self.__tank_tier)

                        self.team_info['allies_rating'] = g_clanAPI.get_clan_rating(self.team_info['id_allies'], self.__tank_tier, self.__guiType)
                        self.team_info['enemies_rating'] = g_clanAPI.get_clan_rating(self.team_info['id_enemies'], self.__tank_tier, self.__guiType)
                        print_debug("[ArenaInfoProvider] Ratings - allies: %s, enemies: %s" % (self.team_info['allies_rating'], self.team_info['enemies_rating']))
                        
                        Elo = g_eloCalc.calculate_elo_changes(self.team_info['allies_rating'], self.team_info['enemies_rating'])
                        self.team_info['elo_plus'] = Elo[0]
                        self.team_info['elo_minus'] = Elo[1]
                        print_debug("[ArenaInfoProvider] ELO changes - plus: %s, minus: %s" % (self.team_info['elo_plus'], self.team_info['elo_minus']))

                        self.team_info['wins_percent'], self.team_info['battles_count'] = g_clanAPI.get_for_last_28_days(self.team_info['id_enemies'], self.__tank_tier, self.__guiType)
                        print_debug("[ArenaInfoProvider] Last 28 days - wins percent: %s, battles count: %s" % (self.team_info['wins_percent'], self.team_info['battles_count']))
                        
                        try:
                            print_debug("[ArenaInfoProvider] Updating/creating text fields")
                            g_multiTextPanel.create_text_fields(
                                self.ON_HOTKEY_PRESSED, 
                                self.team_info['allies'], 
                                self.team_info['enemies'], 
                                self.team_info['allies_rating'], 
                                self.team_info['enemies_rating'], 
                                self.team_info['elo_plus'], 
                                self.team_info['elo_minus'], 
                                self.team_info['wins_percent'], 
                                self.team_info['battles_count']
                            )
                        except Exception as ex:
                            print_error("[ArenaInfoProvider] Error creating/updating text fields: %s" % str(ex))
                    else:
                        print_debug("[ArenaInfoProvider] Invalid GUI type: %d" % self.__guiType)
                else:
                    print_debug("[ArenaInfoProvider] Mod disabled")
                    
            except Exception as e:
                print_error("[ArenaInfoProvider] Error in waitVehicles: %s" % str(e))
                
        waitVehicles()

    def stop(self, *a, **k):
        print_debug("[ArenaInfoProvider] Stopping...")
        self.team_info = {'allies': None, 'enemies': None, 'id_allies': None, 'id_enemies': None,
                          'allies_rating': None, 'enemies_rating': None,
                          'elo_plus': None, 'elo_minus': None, 'wins_percent': None, 'battles_count': None }
        
        try:
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

            if g_configParams.enabled.value:
                print_debug("[ArenaInfoProvider] Mod enabled, checking GUI type...")
                
                if self.__guiType in (15, 16):
                    print_debug("[ArenaInfoProvider] Valid GUI type, preparing text fields...")
                    
                    print_debug("[ArenaInfoProvider] Creating/updating text fields with visibility: %s" % self.ON_HOTKEY_PRESSED)
                    g_multiTextPanel.create_text_fields(
                        self.ON_HOTKEY_PRESSED, 
                        self.team_info['allies'], 
                        self.team_info['enemies'], 
                        self.team_info['allies_rating'], 
                        self.team_info['enemies_rating'], 
                        self.team_info['elo_plus'], 
                        self.team_info['elo_minus'],
                        self.team_info['wins_percent'],
                        self.team_info['battles_count']
                    )
                else:
                    print_debug("[ArenaInfoProvider] Invalid GUI type: %d" % self.__guiType)
            else:
                print_debug("[ArenaInfoProvider] Mod disabled")
                
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

    def set_team_info(self):
        try:
            print_debug("[ArenaInfoProvider] Setting team info...")
            
            arena_dp = BigWorld.player().guiSessionProvider.getArenaDP()
            personal_description = arena_dp.getPersonalDescription()
            
            if self.__playerTeam == 2:
                self.team_info['allies'] = personal_description.getTeamName(2)
                self.team_info['enemies'] = personal_description.getTeamName(1)
                print_debug("[ArenaInfoProvider] Player on team 2 - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
            else: 
                self.team_info['allies'] = personal_description.getTeamName(1)
                self.team_info['enemies'] = personal_description.getTeamName(2)
                print_debug("[ArenaInfoProvider] Player on team 1 - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
                
        except Exception as e:
            print_error("[ArenaInfoProvider] Error setting team info: %s" % str(e))
            self.team_info['allies'] = "Unknown"
            self.team_info['enemies'] = "Unknown"

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