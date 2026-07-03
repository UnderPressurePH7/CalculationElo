# -*- coding: utf-8 -*-
import Event
import BigWorld
from ..settings import g_config
from ..utils import logger, calculate_elo_changes, get_battle_level


class ClanStateManager(object):

    def __init__(self, clanApi):
        self._clanApi = clanApi
        self._view = None

        self._state = self._default_state()
        self._battleSessionId = 0
        self.onStateChanged = Event.Event()

        self._pendingRequests = {
            'allies_clan_id': False,
            'enemies_clan_id': False,
            'allies_info': False,
            'enemies_info': False
        }

    @staticmethod
    def _default_state():
        return {
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

    def set_view(self, view):
        self._view = view
        logger.debug('[ClanStateManager] View set: %s', 'Yes' if view else 'No')

    def fini(self):
        self._battleSessionId += 1
        self._state = self._default_state()
        self._pendingRequests = {
            'allies_clan_id': False,
            'enemies_clan_id': False,
            'allies_info': False,
            'enemies_info': False
        }
        self._view = None
        self._clanApi = None
        self.onStateChanged.clear()

    def reset_state(self):
        self._battleSessionId += 1
        self._state = self._default_state()
        self._pendingRequests = {
            'allies_clan_id': False,
            'enemies_clan_id': False,
            'allies_info': False,
            'enemies_info': False
        }
        logger.debug('[ClanStateManager] State reset (session=%s)', self._battleSessionId)

    def initialize_battle(self, alliesName, enemiesName, tankTier):
        try:
            logger.debug('[ClanStateManager] === BATTLE INIT === Allies="%s" Enemies="%s" Tier=%s',
                         alliesName, enemiesName, tankTier)

            self.reset_state()

            self._state['allies_name'] = alliesName
            self._state['enemies_name'] = enemiesName
            self._state['tank_tier'] = tankTier

            self._notifyViewUpdate()
            self._fetchClanIds()

        except Exception as e:
            logger.error('[ClanStateManager] Error initializing battle: %s', e)
            import traceback
            logger.error('[ClanStateManager] Traceback: %s', traceback.format_exc())

    def _fetchClanIds(self):
        try:
            alliesName = self._state['allies_name']
            enemiesName = self._state['enemies_name']
            sessionId = self._battleSessionId

            if alliesName and alliesName != 'Unknown':
                self._pendingRequests['allies_clan_id'] = True
                self._clanApi.get_clan_id(
                    alliesName,
                    lambda tag, cid: self._onClanIdReceived('allies', tag, cid, sessionId)
                )

            if enemiesName and enemiesName != 'Unknown':
                self._pendingRequests['enemies_clan_id'] = True
                self._clanApi.get_clan_id(
                    enemiesName,
                    lambda tag, cid: self._onClanIdReceived('enemies', tag, cid, sessionId)
                )

        except Exception as e:
            logger.error('[ClanStateManager] Error fetching clan IDs: %s', e)

    def _onClanIdReceived(self, team, clanTag, clanId, sessionId):
        try:
            if sessionId != self._battleSessionId:
                self._pendingRequests['{}_clan_id'.format(team)] = False
                logger.debug('[ClanStateManager] Stale clan ID response for "%s" (session %s != %s), ignoring',
                             clanTag, sessionId, self._battleSessionId)
                return

            logger.debug('[ClanStateManager] Clan ID for %s "%s": %s', team, clanTag, clanId)

            self._state['{}_clan_id'.format(team)] = clanId
            self._pendingRequests['{}_clan_id'.format(team)] = False

            if clanId:
                self._fetchStrongholdInfo(team, clanId)

            self._notifyViewUpdate()

        except Exception as e:
            logger.error('[ClanStateManager] Error processing clan ID: %s', e)

    def _fetchStrongholdInfo(self, team, clanId):
        try:
            battleLevel = get_battle_level(self._state.get('tank_tier', 10))
            sessionId = self._battleSessionId

            logger.debug('[ClanStateManager] Fetching %s info for clan %s, level %s',
                         team, clanId, battleLevel)

            self._pendingRequests['{}_info'.format(team)] = True

            self._clanApi.get_stronghold_info(
                clanId,
                battleLevel,
                lambda cid, lvl, result: self._onStrongholdInfoReceived(team, cid, lvl, result, sessionId)
            )

        except Exception as e:
            logger.error('[ClanStateManager] Error fetching stronghold info: %s', e)

    def _onStrongholdInfoReceived(self, team, clanId, battleLevel, result, sessionId):
        try:
            if sessionId != self._battleSessionId:
                self._pendingRequests['{}_info'.format(team)] = False
                logger.debug('[ClanStateManager] Stale stronghold response for %s (session %s != %s), ignoring',
                             team, sessionId, self._battleSessionId)
                return

            rating = result.get('elo', 0)
            logger.debug('[ClanStateManager] %s rating: %s', team, rating)

            self._state['{}_rating'.format(team)] = rating
            self._pendingRequests['{}_info'.format(team)] = False

            if team == 'enemies':
                self._state['wins_percent'] = result.get('wins_percent', 0)
                self._state['battles_count'] = result.get('battles_count', 0)

            if self._state['allies_rating'] > 0 and self._state['enemies_rating'] > 0:
                self._calculateEloChanges()

            self._notifyViewUpdate()

        except Exception as e:
            logger.error('[ClanStateManager] Error processing stronghold info: %s', e)

    def _calculateEloChanges(self):
        try:
            alliesRating = self._state['allies_rating']
            enemiesRating = self._state['enemies_rating']

            if alliesRating > 0 and enemiesRating > 0:
                eloPlus, eloMinus = calculate_elo_changes(alliesRating, enemiesRating)
                self._state['elo_plus'] = eloPlus
                self._state['elo_minus'] = eloMinus
                logger.debug('[ClanStateManager] ELO: +%s, %s', eloPlus, eloMinus)

        except Exception as e:
            logger.error('[ClanStateManager] Error calculating ELO: %s', e)

    def _notifyViewUpdate(self):
        try:
            stateCopy = self._state.copy()
            if self._view:
                self._view.updateFromState(stateCopy)
            self.onStateChanged(stateCopy)

        except Exception as e:
            logger.error('[ClanStateManager] Error notifying view: %s', e)

    def get_state(self):
        return self._state.copy()
