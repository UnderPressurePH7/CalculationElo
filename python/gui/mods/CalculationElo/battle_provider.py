# -*- coding: utf-8 -*-
import BigWorld
from PlayerEvents import g_playerEvents
from gui.battle_control import avatar_getter

from .settings import g_config
from .utils import print_debug, print_error


class BattleProvider(object):

    ALLOWED_GUI_TYPES = (15, 16)

    def __init__(self, clanStateManager, eloPanel):
        print_debug("[BattleProvider] Initializing...")
        
        self._arena = None
        self._guiType = None
        self._playerTeam = None
        self._tankTier = None
        
        self._clanStateManager = clanStateManager
        self._eloPanel = eloPanel
        self._retryCount = 0
        self._maxRetries = 5
        self._isBattleActive = False
        self._isStrongholdBattle = False

        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onAvatarBecomeNonPlayer

        print_debug("[BattleProvider] Initialized")

    def fini(self):
        print_debug("[BattleProvider] Finalizing...")
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onAvatarBecomeNonPlayer
            
        except Exception as e:
            print_error("[BattleProvider] Error in fini: {}".format(e))

    def _onAvatarReady(self):
        print_debug("[BattleProvider] Avatar ready")
        try:
            if not g_config.configParams.enabled.value:
                print_debug("[BattleProvider] Mod disabled - skipping")
                return
        except Exception:
            print_error("[BattleProvider] Failed to check config")
            return
            
        try:
            self._retryCount = 0
            self._tryInitializeBattle()
            
        except Exception as e:
            print_error("[BattleProvider] Failed to start battle session: {}".format(e))
            import traceback
            print_error("[BattleProvider] Traceback: {}".format(traceback.format_exc()))

    def _tryInitializeBattle(self):
        print_debug("[BattleProvider] Trying to initialize battle... Retry: {}".format(self._retryCount))
        
        try:
            arena = avatar_getter.getArena()
            
            if arena is None:
                player = BigWorld.player()
                if player:
                    arena = getattr(player, 'arena', None)
            
            if arena is None:
                if self._retryCount < self._maxRetries:
                    self._retryCount += 1
                    BigWorld.callback(1.0, self._tryInitializeBattle)
                else:
                    print_debug("[BattleProvider] Failed to get arena after {} retries".format(self._maxRetries))
                return
            
            self._arena = arena
            self._guiType = getattr(self._arena, 'guiType', None)
            print_debug("[BattleProvider] GUI type: {}".format(self._guiType))
            
            if self._guiType not in self.ALLOWED_GUI_TYPES:
                print_debug("[BattleProvider] Not a stronghold battle (guiType: {}) - panel will NOT be shown".format(self._guiType))
                self._isStrongholdBattle = False
                self._arena = None
                self._guiType = None
                return
            
            print_debug("[BattleProvider] Stronghold battle detected (guiType: {})".format(self._guiType))
            self._isStrongholdBattle = True
            
            if self._eloPanel and not self._isBattleActive:
                self._isBattleActive = True
                self._eloPanel.onBattleStart()
                print_debug("[BattleProvider] EloPanel started for stronghold battle")
            
            player = BigWorld.player()
            self._playerTeam = player.team
            print_debug("[BattleProvider] Player team: {}".format(self._playerTeam))
            
            playerVehicleId = player.playerVehicleID

            if playerVehicleId and playerVehicleId in self._arena.vehicles:
                vehicleData = self._arena.vehicles[playerVehicleId]
                vehicleType = vehicleData.get('vehicleType')

                if vehicleType:
                    self._tankTier = vehicleType.level
                else:
                    self._tankTier = 10
            else:
                self._tankTier = 10

            print_debug("[BattleProvider] Tank tier: {}".format(self._tankTier))

            alliesName, enemiesName = self._getTeamNames()
            print_debug("[BattleProvider] Allies='{}', Enemies='{}'".format(alliesName, enemiesName))
            
            if self._clanStateManager:
                self._clanStateManager.initialize_battle(
                    alliesName,
                    enemiesName,
                    self._tankTier,
                )
            
        except Exception as e:
            print_error("[BattleProvider] Error in _tryInitializeBattle: {}".format(e))
            import traceback
            print_error("[BattleProvider] Traceback: {}".format(traceback.format_exc()))

    def _onAvatarBecomeNonPlayer(self):
        print_debug("[BattleProvider] Avatar become non-player")
        try:
            if not g_config.configParams.enabled.value:
                return
        except Exception:
            print_error("[BattleProvider] Config check failed")
        
        try:
            if self._eloPanel and self._isBattleActive:
                self._eloPanel.onBattleEnd()
                self._isBattleActive = False
                print_debug("[BattleProvider] EloPanel ended")
            
            if self._clanStateManager:
                self._clanStateManager.reset_state()
            
        except Exception as e:
            print_error("[BattleProvider] Failed to stop battle session: {}".format(e))

        finally:
            self._arena = None
            self._guiType = None
            self._playerTeam = None
            self._tankTier = None
            self._retryCount = 0
            self._isStrongholdBattle = False

    def _getTeamNames(self):
        try:
            arenaDP = BigWorld.player().guiSessionProvider.getArenaDP()
            personalDescription = arenaDP.getPersonalDescription()
            
            team1Name = personalDescription.getTeamName(1)
            team2Name = personalDescription.getTeamName(2)

            if self._playerTeam == 2:
                allies = team2Name
                enemies = team1Name
            else:
                allies = team1Name
                enemies = team2Name

            return allies, enemies
                
        except Exception as e:
            print_error("[BattleProvider] Error getting team names: {}".format(str(e)))
            return "Unknown", "Unknown"
