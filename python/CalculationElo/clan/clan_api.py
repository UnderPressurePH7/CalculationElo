# -*- coding: utf-8 -*-
import time

import BigWorld
from urllib import quote
from wg_async import wg_async, AsyncReturn
from ..utils import logger, ApiFallbackRequester, byteify


DEFAULT_WG_APP_ID = '8f04db08e54ff45dbd7d4b7e7de0b76b'

REALM_CONFIG = {
    'EU': {
        'api_hosts': ['https://api.worldoftanks.eu'],
        'wgsh_hosts': ['https://wgsh-woteu.wargaming.net'],
        'stronghold_path': '/game_api/stronghold_info/clan/{clan_id}',
    },
    'NA': {
        'api_hosts': ['https://api.worldoftanks.com'],
        'wgsh_hosts': ['https://wgsh-wotus.wargaming.net'],
        'stronghold_path': '/game_api/stronghold_info/clan/{clan_id}',
    },
    'ASIA': {
        'api_hosts': ['https://api.worldoftanks.asia'],
        'wgsh_hosts': ['https://asia.wargaming.net'],
        'stronghold_path': '/clans/wot/{clan_id}/api/stronghold/',
    },
}

DEFAULT_REALM = 'EU'


def detect_realm():
    try:
        import constants
        realm = getattr(constants, 'AUTH_REALM', None)
        if realm:
            realm = str(realm).upper()
            if realm in REALM_CONFIG:
                logger.debug('[ClanAPI] Detected realm: %s', realm)
                return realm
            logger.debug('[ClanAPI] Unknown realm "%s", falling back to %s', realm, DEFAULT_REALM)
    except Exception as e:
        logger.error('[ClanAPI] Realm detection failed: %s', e)
    return DEFAULT_REALM


WG_API_HOSTS = REALM_CONFIG[DEFAULT_REALM]['api_hosts']
WGSH_HOSTS = REALM_CONFIG[DEFAULT_REALM]['wgsh_hosts']

MAX_CACHE_SIZE = 50
EMPTY_STRONGHOLD_INFO = {'elo': 0, 'wins_percent': 0, 'battles_count': 0}
CLAN_ID_CACHE_TTL = 3600.0


def _normalize_tag(clanTag):
    try:
        return str(clanTag).strip().upper()
    except Exception:
        return ''


def _value_or_zero(value):
    return 0 if value is None else value


def _find_clan_id(dataList, clanTag):
    if not isinstance(dataList, (list, tuple)):
        return None

    expectedTag = str(clanTag).strip().upper()
    for clanData in dataList:
        if not isinstance(clanData, dict):
            continue
        actualTag = str(clanData.get('tag', '')).strip().upper()
        if actualTag == expectedTag:
            return clanData.get('clan_id')
    return None


def _parse_wgsh_stronghold(data, battleLevel):
    if not isinstance(data, dict):
        return None

    stats = data.get('stats')
    if not isinstance(stats, dict):
        return None

    levelStats = stats.get(str(battleLevel))
    if not isinstance(levelStats, dict):
        return None

    sortiesData = levelStats.get('sorties')
    if not isinstance(sortiesData, dict):
        sortiesData = {}

    return {
        'elo': _value_or_zero(levelStats.get('elo')),
        'wins_percent': _value_or_zero(
            sortiesData.get('wins_percent_for_last_28_days')
        ),
        'battles_count': _value_or_zero(
            sortiesData.get('battles_count_for_last_28_days')
        )
    }


def _parse_asia_stronghold(data, battleLevel):
    if not isinstance(data, dict):
        return None

    stronghold = data.get('stronghold')
    if not isinstance(stronghold, dict):
        return None

    levelKey = str(battleLevel)
    eloKey = 'esh_{}'.format(levelKey)
    if eloKey not in stronghold:
        return None

    sorties = stronghold.get('sorties')
    if not isinstance(sorties, dict):
        sorties = {}

    sortiesData = sorties.get('level_{}'.format(levelKey))
    if not isinstance(sortiesData, dict):
        sortiesData = {}

    return {
        'elo': _value_or_zero(stronghold.get(eloKey)),
        'wins_percent': _value_or_zero(sortiesData.get('win_rate')),
        'battles_count': _value_or_zero(sortiesData.get('battles_count'))
    }


class ClanAPI(object):

    def __init__(self, appId=None, apiHosts=None, wgshHosts=None, realm=None):
        self._realm = (realm or detect_realm()).upper()
        cfg = REALM_CONFIG.get(self._realm, REALM_CONFIG[DEFAULT_REALM])

        self._appId = appId or DEFAULT_WG_APP_ID
        self._strongholdPath = cfg['stronghold_path']
        apiHostList = apiHosts or cfg['api_hosts']
        wgshHostList = wgshHosts or cfg['wgsh_hosts']
        self._apiRequester = ApiFallbackRequester(apiHostList)
        self._wgshRequester = ApiFallbackRequester(wgshHostList)

        logger.debug('[ClanAPI] Realm=%s api=%s wgsh=%s',
                     self._realm, apiHostList, wgshHostList)

        self._clanIdCache = {}
        self._strongholdCache = {}
        self._clanIdWaiters = {}
        self._strongholdWaiters = {}

        self._generation = 0
        self._finalized = False

    @property
    def realm(self):
        return self._realm

    def _isCurrent(self, generation):
        return not self._finalized and generation == self._generation

    def _deliver(self, generation, callback, args):
        def _fire():
            if not self._isCurrent(generation):
                return
            try:
                callback(*args)
            except Exception as e:
                logger.error('[ClanAPI] Callback failed: %s', e)

        BigWorld.callback(0.0, _fire)

    def _trimCache(self, cache):
        overflow = len(cache) - MAX_CACHE_SIZE
        if overflow <= 0:
            return
        ordered = sorted(cache.items(), key=lambda item: item[1][1])
        for key, _ in ordered[:overflow]:
            cache.pop(key, None)


    @wg_async
    def _getClanIdAsync(self, clanTag):
        path = '/wot/clans/list/?application_id={}&search={}'.format(
            quote(str(self._appId), safe=''), quote(str(clanTag), safe='')
        )

        try:
            status, body = yield self._apiRequester(path, timeout=10.0)

            if not body:
                raise AsyncReturn(None)

            import json
            rawData = json.loads(body) if isinstance(body, (str, bytes)) else body
            data = byteify(rawData)

            if data and data.get('status') == 'ok' and data.get('meta', {}).get('count', 0) > 0:
                dataList = data.get('data', [])
                clanId = _find_clan_id(dataList, clanTag)
                if clanId:
                    logger.debug('[ClanAPI] Clan ID for "%s": %s', clanTag, clanId)
                    raise AsyncReturn(clanId)

            logger.error('[ClanAPI] No clan found for tag: %s', clanTag)
            raise AsyncReturn(None)

        except AsyncReturn:
            raise
        except Exception as e:
            logger.error('[ClanAPI] Error fetching clan ID for "%s": %s', clanTag, e)
            raise AsyncReturn(None)

    def _readClanId(self, key, allowStale=False):
        entry = self._clanIdCache.get(key)
        if entry is None:
            return None
        clanId, timestamp = entry
        if not allowStale and (time.time() - timestamp) > CLAN_ID_CACHE_TTL:
            return None
        return clanId

    def get_clan_id(self, clanTag, callback):
        generation = self._generation
        key = _normalize_tag(clanTag)

        if self._finalized or not key:
            self._deliver(generation, callback, (clanTag, None))
            return

        cachedId = self._readClanId(key)
        if cachedId is not None:
            logger.debug('[ClanAPI] Clan ID cache hit for "%s": %s', key, cachedId)
            self._deliver(generation, callback, (clanTag, cachedId))
            return

        waiters = self._clanIdWaiters.get(key)
        if waiters is not None:
            logger.debug('[ClanAPI] Joined in-flight clan ID request for "%s"', key)
            waiters.append((clanTag, callback))
            return

        self._clanIdWaiters[key] = [(clanTag, callback)]

        @wg_async
        def worker():
            clanId = None
            try:
                clanId = yield self._getClanIdAsync(clanTag)
            except Exception as e:
                logger.error('[ClanAPI] Error in get_clan_id: %s', e)
                clanId = None
            self._finishClanId(generation, key, clanId)

        try:
            worker()
        except Exception as e:
            logger.error('[ClanAPI] Failed to start clan ID worker: %s', e)
            self._finishClanId(generation, key, None)

    def _finishClanId(self, generation, key, clanId):
        waiters = self._clanIdWaiters.pop(key, [])

        if not self._isCurrent(generation):
            logger.debug('[ClanAPI] Dropping stale clan ID result for "%s"', key)
            return

        if clanId:
            self._clanIdCache[key] = (clanId, time.time())
            self._trimCache(self._clanIdCache)
            resolved = clanId
        else:
            resolved = self._readClanId(key, allowStale=True)
            if resolved is not None:
                logger.debug('[ClanAPI] Falling back to cached clan ID for "%s": %s', key, resolved)

        for originalTag, callback in waiters:
            self._deliver(generation, callback, (originalTag, resolved))

    @wg_async
    def _getStrongholdInfoAsync(self, clanId):
        if not clanId:
            raise AsyncReturn(None)

        path = self._strongholdPath.format(clan_id=clanId)

        try:
            status, body = yield self._wgshRequester(path, timeout=10.0)

            if not body:
                logger.error('[ClanAPI] Empty stronghold response for clan %s', clanId)
                raise AsyncReturn(None)

            import json
            rawData = json.loads(body) if isinstance(body, (str, bytes)) else body
            data = byteify(rawData)

            if not isinstance(data, dict):
                logger.error('[ClanAPI] Invalid stronghold response for clan %s', clanId)
                raise AsyncReturn(None)

            raise AsyncReturn(data)

        except AsyncReturn:
            raise
        except Exception as e:
            logger.error('[ClanAPI] Error fetching stronghold info for clan %s: %s', clanId, e)
            raise AsyncReturn(None)

    def _parseStrongholdInfo(self, data, battleLevel):
        if self._realm == 'ASIA':
            return _parse_asia_stronghold(data, battleLevel)
        return _parse_wgsh_stronghold(data, battleLevel)

    def get_stronghold_info(self, clanId, battleLevel, callback):
        generation = self._generation

        if self._finalized or not clanId:
            self._deliver(generation, callback,
                          (clanId, battleLevel, EMPTY_STRONGHOLD_INFO.copy()))
            return

        waiters = self._strongholdWaiters.get(clanId)
        if waiters is not None:
            logger.debug('[ClanAPI] Joined in-flight stronghold request for clan %s', clanId)
            waiters.append((battleLevel, callback))
            return

        self._strongholdWaiters[clanId] = [(battleLevel, callback)]

        @wg_async
        def worker():
            data = None
            try:
                data = yield self._getStrongholdInfoAsync(clanId)
            except Exception as e:
                logger.error('[ClanAPI] Error in get_stronghold_info: %s', e)
                data = None
            self._finishStronghold(generation, clanId, data)

        try:
            worker()
        except Exception as e:
            logger.error('[ClanAPI] Failed to start stronghold worker: %s', e)
            self._finishStronghold(generation, clanId, None)

    def _finishStronghold(self, generation, clanId, data):
        waiters = self._strongholdWaiters.pop(clanId, [])

        if not self._isCurrent(generation):
            logger.debug('[ClanAPI] Dropping stale stronghold result for clan %s', clanId)
            return

        now = time.time()
        for battleLevel, callback in waiters:
            cacheKey = '{}_{}'.format(clanId, battleLevel)
            result = self._parseStrongholdInfo(data, battleLevel) if data is not None else None

            if result is not None:
                self._strongholdCache[cacheKey] = (result, now)
                self._trimCache(self._strongholdCache)
                payload = result
            else:
                entry = self._strongholdCache.get(cacheKey)
                if entry is not None:
                    logger.debug('[ClanAPI] Falling back to cached stronghold info for %s', cacheKey)
                    payload = entry[0]
                else:
                    logger.error('[ClanAPI] Stronghold data has no level %s for clan %s',
                                 battleLevel, clanId)
                    payload = EMPTY_STRONGHOLD_INFO

            self._deliver(generation, callback, (clanId, battleLevel, dict(payload)))

    def clear_cache(self):
        self._generation += 1
        self._clanIdCache.clear()
        self._strongholdCache.clear()
        self._clanIdWaiters.clear()
        self._strongholdWaiters.clear()
        logger.debug('[ClanAPI] Cache cleared (generation=%s)', self._generation)

    def fini(self):
        self._finalized = True
        self.clear_cache()
        logger.debug('[ClanAPI] Finalized')
