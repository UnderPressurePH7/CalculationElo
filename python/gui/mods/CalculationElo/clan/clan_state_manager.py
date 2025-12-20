# -*- coding: utf-8 -*-
import BigWorld
from ..settings import g_config
from ..utils import print_debug, print_error, calculate_elo_changes


class ClanStateManager(object):
    
    def __init__(self, clanApi):
        self._clanApi = clanApi
        self._view = None
        
        self._state = {
            'allies_name': 'Unknown',
            'enemies_name': 'Unknown',
            'allies_clan_id': None,
            'enemies_clan_id': None,
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0,
            'tank_tier': 10
        }
        
        self._pendingRequests = {
            'allies_clan_id': False,
            'enemies_clan_id': False,
            'allies_rating': False,
            'enemies_rating': False,
            'stats': False
        }
        
        print_debug("[ClanStateManager] Initialized")
    
    def set_view(self, view):
        self._view = view
        print_debug("[ClanStateManager] View set: {}".format('Yes' if view else 'No'))
    
    def reset_state(self):
        self._state = {
            'allies_name': 'Unknown',
            'enemies_name': 'Unknown',
            'allies_clan_id': None,
            'enemies_clan_id': None,
            'allies_rating': 0,
            'enemies_rating': 0,
            'elo_plus': 0,
            'elo_minus': 0,
            'wins_percent': 0,
            'battles_count': 0,
            'tank_tier': 10
        }
        
        self._pendingRequests = {
            'allies_clan_id': False,
            'enemies_clan_id': False,
            'allies_rating': False,
            'enemies_rating': False,
            'stats': False
        }
        
        print_debug("[ClanStateManager] State reset")
    
    def initialize_battle(self, alliesName, enemiesName, tankTier):
        try:
            print_debug("[ClanStateManager] ========== BATTLE INITIALIZATION ==========")
            print_debug("[ClanStateManager] Allies: '{}'".format(alliesName))
            print_debug("[ClanStateManager] Enemies: '{}'".format(enemiesName))
            print_debug("[ClanStateManager] Tank tier: {}".format(tankTier))

            self.reset_state()
            
            self._state['allies_name'] = alliesName
            self._state['enemies_name'] = enemiesName
            self._state['tank_tier'] = tankTier
            
            self._notifyViewUpdate()
            self._fetchClanIds()
            
            print_debug("[ClanStateManager] Battle initialized, fetching clan data...")
            
        except Exception as e:
            print_error("[ClanStateManager] Error initializing battle: {}".format(e))
            import traceback
            print_error("[ClanStateManager] Traceback: {}".format(traceback.format_exc()))
    
    def _fetchClanIds(self):
        try:
            alliesName = self._state['allies_name']
            enemiesName = self._state['enemies_name']
            
            if alliesName and alliesName != 'Unknown':
                self._pendingRequests['allies_clan_id'] = True
                self._clanApi.get_clan_id(alliesName, self._onClanIdReceived)
            
            if enemiesName and enemiesName != 'Unknown':
                self._pendingRequests['enemies_clan_id'] = True
                self._clanApi.get_clan_id(enemiesName, self._onClanIdReceived)
                
        except Exception as e:
            print_error("[ClanStateManager] Error fetching clan IDs: {}".format(e))
    
    def _onClanIdReceived(self, clanTag, clanId):
        try:
            print_debug("[ClanStateManager] Received clan ID for '{}': {}".format(clanTag, clanId))
            
            isAllies = clanTag == self._state['allies_name']
            isEnemies = clanTag == self._state['enemies_name']
            
            if isAllies:
                self._state['allies_clan_id'] = clanId
                self._pendingRequests['allies_clan_id'] = False
                
                if clanId:
                    self._fetchClanRating('allies', clanId)
            
            elif isEnemies:
                self._state['enemies_clan_id'] = clanId
                self._pendingRequests['enemies_clan_id'] = False
                
                if clanId:
                    self._fetchClanRating('enemies', clanId)
                    self._fetchClanStats(clanId)
            
            self._notifyViewUpdate()
            
        except Exception as e:
            print_error("[ClanStateManager] Error processing clan ID: {}".format(e))
    
    def _fetchClanRating(self, team, clanId):
        try:
            tankTier = self._state.get('tank_tier', 10)
            
            if tankTier <= 6:
                battleLevel = 6
            elif tankTier <= 8:
                battleLevel = 8
            else:
                battleLevel = 10
            
            print_debug("[ClanStateManager] Fetching {} rating for clan_id: {}, level: {}".format(
                team, clanId, battleLevel))
            
            self._pendingRequests['{}_rating'.format(team)] = True
            
            self._clanApi.get_clan_rating(
                clanId,
                battleLevel,
                battleLevel,
                lambda cid, lvl, gui, rating: self._onClanRatingReceived(team, cid, lvl, rating)
            )
            
        except Exception as e:
            print_error("[ClanStateManager] Error fetching clan rating: {}".format(e))
    
    def _onClanRatingReceived(self, team, clanId, battleLevel, rating):
        try:
            print_debug("[ClanStateManager] Received {} rating: {}".format(team, rating))
            
            self._state['{}_rating'.format(team)] = rating
            self._pendingRequests['{}_rating'.format(team)] = False
            
            if self._state['allies_rating'] > 0 and self._state['enemies_rating'] > 0:
                self._calculateEloChanges()
            
            self._notifyViewUpdate()
            
        except Exception as e:
            print_error("[ClanStateManager] Error processing clan rating: {}".format(e))
    
    def _calculateEloChanges(self):
        try:
            alliesRating = self._state['allies_rating']
            enemiesRating = self._state['enemies_rating']
            
            if alliesRating > 0 and enemiesRating > 0:
                eloPlus, eloMinus = calculate_elo_changes(alliesRating, enemiesRating)
                
                self._state['elo_plus'] = eloPlus
                self._state['elo_minus'] = eloMinus
                
                print_debug("[ClanStateManager] ELO changes: +{}, {}".format(eloPlus, eloMinus))
                
                self._notifyViewUpdate()
            
        except Exception as e:
            print_error("[ClanStateManager] Error calculating ELO changes: {}".format(e))
    
    def _fetchClanStats(self, clanId):
        try:
            tankTier = self._state.get('tank_tier', 10)
            
            if tankTier <= 6:
                battleLevel = 6
            elif tankTier <= 8:
                battleLevel = 8
            else:
                battleLevel = 10
            
            print_debug("[ClanStateManager] Fetching enemy stats for clan_id: {}".format(clanId))
            
            self._pendingRequests['stats'] = True
            
            self._clanApi.get_for_last_28_days(
                clanId,
                battleLevel,
                self._onClanStatsReceived
            )
            
        except Exception as e:
            print_error("[ClanStateManager] Error fetching clan stats: {}".format(e))
    
    def _onClanStatsReceived(self, clanId, battleLevel, winsPercent, battlesCount):
        try:
            print_debug("[ClanStateManager] Received enemy stats: {}% wins, {} battles".format(
                winsPercent, battlesCount))
            
            self._state['wins_percent'] = winsPercent
            self._state['battles_count'] = battlesCount
            self._pendingRequests['stats'] = False
            
            self._notifyViewUpdate()
            
        except Exception as e:
            print_error("[ClanStateManager] Error processing clan stats: {}".format(e))
    
    def _notifyViewUpdate(self):
        try:
            print_debug("[ClanStateManager] Notifying view update")
            print_debug("[ClanStateManager]     Allies: '{}' ({})".format(
                self._state['allies_name'], 
                self._state['allies_rating']))
            print_debug("[ClanStateManager]     Enemies: '{}' ({})".format(
                self._state['enemies_name'], 
                self._state['enemies_rating']))
            print_debug("[ClanStateManager]     ELO: +{}, {}".format(
                self._state['elo_plus'],
                self._state['elo_minus']))
            
            if self._view:
                self._view.updateFromState(self._state)
                print_debug("[ClanStateManager] View notified")
            else:
                print_debug("[ClanStateManager] No view to notify")
            
        except Exception as e:
            print_error("[ClanStateManager] Error notifying view update: {}".format(e))
            import traceback
            print_error("[ClanStateManager] Traceback: {}".format(traceback.format_exc()))
    
    def get_state(self):
        return self._state.copy()
