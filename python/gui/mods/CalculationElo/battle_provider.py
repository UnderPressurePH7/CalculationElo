# -*- coding: utf-8 -*-
import weakref
import BigWorld
import constants
import BattleReplay
from gui.battle_control import avatar_getter

from .settings import g_config
from .utils import logger, override, restore_overrides


STRONGHOLD_GUI_TYPES = (
    constants.ARENA_GUI_TYPE.SORTIE_2,
    constants.ARENA_GUI_TYPE.FORT_BATTLE_2,
)


def isBattleStronghold():
    try:
        player = BigWorld.player()
        if not player or not hasattr(player, 'arena') or player.arena is None:
            return False
        return player.arena.guiType in STRONGHOLD_GUI_TYPES
    except Exception:
        return False


class BattleProvider(object):

    MAX_RETRIES = 15
    _hooked = False
    _instance = None

    def __init__(self, clanStateManager, eloPanel):
        self._arena = None
        self._guiType = None
        self._playerTeam = None
        self._tankTier = None

        self._clanStateManager = clanStateManager
        self._eloPanel = eloPanel
        self._retryCount = 0
        self._isBattleActive = False
        self._isStrongholdBattle = False
        self._battleSessionId = 0
        self._fallbackSubscribed = False

        BattleProvider._instance = self
        self._installOverrides()
        logger.debug('[BattleProvider] Initialized')

    def _installOverrides(self):
        if BattleProvider._hooked:
            return

        try:
            from Avatar import PlayerAvatar

            @override(PlayerAvatar, 'onBecomePlayer')
            def hooked_onBecomePlayer(baseMethod, baseObject, *a, **kw):
                baseMethod(baseObject, *a, **kw)
                inst = BattleProvider._instance
                if inst:
                    inst._onAvatarReady()

            @override(PlayerAvatar, 'onBecomeNonPlayer')
            def hooked_onBecomeNonPlayer(baseMethod, baseObject, *a, **kw):
                inst = BattleProvider._instance
                if inst:
                    inst._onAvatarBecomeNonPlayer()
                baseMethod(baseObject, *a, **kw)

            @override(BattleReplay.BattleReplay, 'onReplayFinished')
            def hooked_onReplayFinished(baseMethod, baseObject, *a, **kw):
                inst = BattleProvider._instance
                if inst:
                    inst._onAvatarBecomeNonPlayer()
                return baseMethod(baseObject, *a, **kw)

            BattleProvider._hooked = True
            logger.debug('[BattleProvider] PlayerAvatar/BattleReplay overrides installed')

        except Exception as e:
            logger.error('[BattleProvider] Failed to install overrides: %s', e)
            import traceback
            logger.error('[BattleProvider] Traceback: %s', traceback.format_exc())
            self._installEventFallback()

    def _installEventFallback(self):
        try:
            from PlayerEvents import g_playerEvents
            g_playerEvents.onAvatarReady += self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer += self._onAvatarBecomeNonPlayer
            self._fallbackSubscribed = True
            logger.debug('[BattleProvider] Fallback: using g_playerEvents')
        except Exception as e:
            logger.error('[BattleProvider] Fallback subscription also failed: %s', e)

    def fini(self):
        self._battleSessionId += 1

        if BattleProvider._instance is self:
            BattleProvider._instance = None

        if self._fallbackSubscribed:
            try:
                from PlayerEvents import g_playerEvents
                g_playerEvents.onAvatarReady -= self._onAvatarReady
                g_playerEvents.onAvatarBecomeNonPlayer -= self._onAvatarBecomeNonPlayer
                self._fallbackSubscribed = False
            except Exception as e:
                logger.error('[BattleProvider] Error in fini: %s', e)

        restore_overrides()
        BattleProvider._hooked = False

        self._clanStateManager = None
        self._eloPanel = None

    def _onAvatarReady(self):
        try:
            if not g_config.configParams.enabled.value:
                return
        except Exception:
            logger.error('[BattleProvider] Failed to check config')
            return

        try:
            self._battleSessionId += 1
            self._retryCount = 0
            self._tryInitializeBattle()
        except Exception as e:
            logger.error('[BattleProvider] Failed to start battle session: %s', e)

    def _tryInitializeBattle(self):
        sessionId = self._battleSessionId

        try:
            player = BigWorld.player()
            if player is None:
                self._scheduleRetry(sessionId, '_tryInitializeBattle', 'player is None')
                return

            arena = getattr(player, 'arena', None)
            if arena is None:
                arena = avatar_getter.getArena()

            if arena is None:
                self._scheduleRetry(sessionId, '_tryInitializeBattle', 'arena is None')
                return

            if not hasattr(player, 'team') or not hasattr(player, 'playerVehicleID'):
                self._scheduleRetry(sessionId, '_tryInitializeBattle',
                                    'player attributes not ready (team/playerVehicleID)')
                return

            self._arena = arena
            self._guiType = getattr(self._arena, 'guiType', None)

            if self._guiType not in STRONGHOLD_GUI_TYPES:
                logger.debug('[BattleProvider] Not a stronghold battle (guiType: %s)', self._guiType)
                self._isStrongholdBattle = False
                self._arena = None
                self._guiType = None
                return

            logger.debug('[BattleProvider] Stronghold battle detected (guiType: %s)', self._guiType)
            self._isStrongholdBattle = True

            if self._eloPanel and not self._isBattleActive:
                self._isBattleActive = True
                self._eloPanel.onBattleStart()

            self._playerTeam = player.team

            playerVehicleId = player.playerVehicleID
            if playerVehicleId and playerVehicleId in self._arena.vehicles:
                vehicleData = self._arena.vehicles[playerVehicleId]
                vehicleType = vehicleData.get('vehicleType')
                self._tankTier = vehicleType.level if vehicleType else 10
            else:
                self._tankTier = 10

            logger.debug('[BattleProvider] Team=%s, Tier=%s', self._playerTeam, self._tankTier)

            alliesName, enemiesName = self._getTeamNames()
            logger.debug('[BattleProvider] Allies="%s", Enemies="%s"', alliesName, enemiesName)

            if not alliesName or alliesName == 'Unknown' or not enemiesName or enemiesName == 'Unknown':
                self._scheduleRetry(sessionId, '_tryInitializeBattleNames',
                                    'team names not ready (allies="%s", enemies="%s")' % (alliesName, enemiesName))
                return

            self._finalizeBattleInit(alliesName, enemiesName)

        except Exception as e:
            logger.error('[BattleProvider] Error in _tryInitializeBattle: %s', e)
            import traceback
            logger.error('[BattleProvider] Traceback: %s', traceback.format_exc())

    def _tryInitializeBattleNames(self):
        sessionId = self._battleSessionId

        try:
            if self._arena is None:
                logger.debug('[BattleProvider] Arena lost during name retry, aborting')
                return

            alliesName, enemiesName = self._getTeamNames()

            if not alliesName or alliesName == 'Unknown' or not enemiesName or enemiesName == 'Unknown':
                self._scheduleRetry(sessionId, '_tryInitializeBattleNames',
                                    'team names still not ready (allies="%s", enemies="%s")' % (alliesName, enemiesName))
                return

            self._finalizeBattleInit(alliesName, enemiesName)

        except Exception as e:
            logger.error('[BattleProvider] Error in _tryInitializeBattleNames: %s', e)
            import traceback
            logger.error('[BattleProvider] Traceback: %s', traceback.format_exc())

    def _finalizeBattleInit(self, alliesName, enemiesName):
        if self._clanStateManager:
            self._clanStateManager.initialize_battle(alliesName, enemiesName, self._tankTier)

    def _scheduleRetry(self, sessionId, methodName, reason):
        if self._retryCount < self.MAX_RETRIES:
            self._retryCount += 1
            logger.debug('[BattleProvider] Retry %s/%s (%s), waiting...',
                         self._retryCount, self.MAX_RETRIES, reason)

            ref = weakref.ref(self)

            def _retryCallback():
                inst = ref()
                if inst is None:
                    return
                if inst._battleSessionId != sessionId:
                    logger.debug('[BattleProvider] Stale retry (session changed), ignoring')
                    return
                method = getattr(inst, methodName, None)
                if method:
                    method()

            BigWorld.callback(0.5, _retryCallback)
        else:
            logger.error('[BattleProvider] Failed after %s retries. Last reason: %s',
                         self.MAX_RETRIES, reason)

    def _onAvatarBecomeNonPlayer(self):
        self._battleSessionId += 1

        try:
            if not g_config.configParams.enabled.value:
                return
        except Exception:
            pass

        try:
            if self._eloPanel and self._isBattleActive:
                self._eloPanel.onBattleEnd()
                self._isBattleActive = False

            if self._clanStateManager:
                self._clanStateManager.reset_state()

        except Exception as e:
            logger.error('[BattleProvider] Failed to stop battle session: %s', e)

        finally:
            self._arena = None
            self._guiType = None
            self._playerTeam = None
            self._tankTier = None
            self._retryCount = 0
            self._isStrongholdBattle = False

    def _getTeamNames(self):
        try:
            player = BigWorld.player()
            if not player:
                return 'Unknown', 'Unknown'

            guiSessionProvider = getattr(player, 'guiSessionProvider', None)
            if guiSessionProvider is None:
                return 'Unknown', 'Unknown'

            arenaDP = guiSessionProvider.getArenaDP()
            if arenaDP is None:
                return 'Unknown', 'Unknown'

            personalDescription = arenaDP.getPersonalDescription()
            if personalDescription is None:
                return 'Unknown', 'Unknown'

            team1Name = personalDescription.getTeamName(1) or ''
            team2Name = personalDescription.getTeamName(2) or ''

            if not team1Name.strip() or not team2Name.strip():
                return 'Unknown', 'Unknown'

            if self._playerTeam == 2:
                return team2Name, team1Name
            return team1Name, team2Name

        except Exception as e:
            logger.error('[BattleProvider] Error getting team names: %s', e)
            return 'Unknown', 'Unknown'
