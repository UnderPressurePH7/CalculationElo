# -*- coding: utf-8 -*-
import BigWorld
from urllib import quote
from wg_async import wg_async, AsyncReturn
from ..utils import logger, fetch_data_with_retry, get_battle_level, ApiFallbackRequester, byteify


DEFAULT_WG_APP_ID = '8f04db08e54ff45dbd7d4b7e7de0b76b'

WG_API_HOSTS = [
    'https://api.worldoftanks.eu',
]

WGSH_HOSTS = [
    'https://wgsh-woteu.wargaming.net',
]


class ClanAPI(object):

    def __init__(self, appId=None, apiHosts=None, wgshHosts=None):
        self._appId = appId or DEFAULT_WG_APP_ID
        self._apiRequester = ApiFallbackRequester(apiHosts or WG_API_HOSTS)
        self._wgshRequester = ApiFallbackRequester(wgshHosts or WGSH_HOSTS)

        self._clanIdCache = {}
        self._strongholdCache = {}

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
                if dataList:
                    clanId = dataList[0].get('clan_id')
                    logger.debug('[ClanAPI] Clan ID for "%s": %s', clanTag, clanId)
                    raise AsyncReturn(clanId)

            logger.error('[ClanAPI] No clan found for tag: %s', clanTag)
            raise AsyncReturn(None)

        except AsyncReturn:
            raise
        except Exception as e:
            logger.error('[ClanAPI] Error fetching clan ID for "%s": %s', clanTag, e)
            raise AsyncReturn(None)

    def get_clan_id(self, clanTag, callback):
        @wg_async
        def worker():
            try:
                clanId = yield self._getClanIdAsync(clanTag)
                if clanId:
                    self._clanIdCache[clanTag] = clanId
                    BigWorld.callback(0.0, lambda: callback(clanTag, clanId))
                elif clanTag in self._clanIdCache:
                    BigWorld.callback(0.0, lambda: callback(clanTag, self._clanIdCache[clanTag]))
                else:
                    BigWorld.callback(0.0, lambda: callback(clanTag, None))
            except Exception as e:
                logger.error('[ClanAPI] Error in get_clan_id: %s', e)
                cached = self._clanIdCache.get(clanTag)
                BigWorld.callback(0.0, lambda: callback(clanTag, cached))

        worker()

    @wg_async
    def _getStrongholdInfoAsync(self, clanId):
        if not clanId:
            raise AsyncReturn(None)

        path = '/game_api/stronghold_info/clan/{}'.format(clanId)

        try:
            status, body = yield self._wgshRequester(path, timeout=10.0)

            if not body:
                logger.error('[ClanAPI] Empty stronghold response for clan %s', clanId)
                raise AsyncReturn(None)

            import json
            rawData = json.loads(body) if isinstance(body, (str, bytes)) else body
            data = byteify(rawData)

            if not data or 'stats' not in data:
                logger.error('[ClanAPI] Invalid stronghold response for clan %s', clanId)
                raise AsyncReturn(None)

            raise AsyncReturn(data)

        except AsyncReturn:
            raise
        except Exception as e:
            logger.error('[ClanAPI] Error fetching stronghold info for clan %s: %s', clanId, e)
            raise AsyncReturn(None)

    def get_stronghold_info(self, clanId, battleLevel, callback):
        cacheKey = '{}_{}'.format(clanId, battleLevel)

        @wg_async
        def worker():
            try:
                data = yield self._getStrongholdInfoAsync(clanId)

                if data and 'stats' in data and str(battleLevel) in data['stats']:
                    levelStats = data['stats'][str(battleLevel)]

                    eloRating = levelStats.get('elo', 0)
                    sortiesData = levelStats.get('sorties', {})
                    winsPercent = sortiesData.get('wins_percent_for_last_28_days', 0)
                    battlesCount = sortiesData.get('battles_count_for_last_28_days', 0)

                    result = {
                        'elo': eloRating,
                        'wins_percent': winsPercent,
                        'battles_count': battlesCount
                    }

                    self._strongholdCache[cacheKey] = result
                    BigWorld.callback(0.0, lambda: callback(clanId, battleLevel, result))

                elif cacheKey in self._strongholdCache:
                    cached = self._strongholdCache[cacheKey]
                    BigWorld.callback(0.0, lambda: callback(clanId, battleLevel, cached))
                else:
                    empty = {'elo': 0, 'wins_percent': 0, 'battles_count': 0}
                    BigWorld.callback(0.0, lambda: callback(clanId, battleLevel, empty))

            except Exception as e:
                logger.error('[ClanAPI] Error in get_stronghold_info: %s', e)
                cached = self._strongholdCache.get(cacheKey,
                    {'elo': 0, 'wins_percent': 0, 'battles_count': 0})
                BigWorld.callback(0.0, lambda: callback(clanId, battleLevel, cached))

        worker()

    def clear_cache(self):
        self._clanIdCache.clear()
        self._strongholdCache.clear()
        logger.debug('[ClanAPI] Cache cleared')

    def fini(self):
        self.clear_cache()
        logger.debug('[ClanAPI] Finalized')
