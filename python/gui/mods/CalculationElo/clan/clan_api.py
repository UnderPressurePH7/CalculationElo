# -*- coding: utf-8 -*-
import BigWorld
from wg_async import wg_async, AsyncReturn
from ..utils import print_debug, print_error, fetch_data_with_retry


class ClanAPI(object):

    def __init__(self):
        self.wgKey = '8f04db08e54ff45dbd7d4b7e7de0b76b'
        self.clanIdCache = {}
        self.clanRatingCache = {}
        self.clanStatsCache = {}

    @wg_async
    def _getClanIdAsync(self, clanTag):
        url = 'https://api.worldoftanks.eu/wot/clans/list/?application_id={}&search={}'.format(
            self.wgKey, clanTag
        )

        try:
            data = yield fetch_data_with_retry(url)

            if data and data.get('status') == 'ok' and data.get('meta', {}).get('count', 0) > 0:
                clanId = data['data'][0].get('clan_id')
                print_debug("[ClanAPI] Clan ID for tag '{}': {}".format(clanTag, clanId))
                raise AsyncReturn(clanId)
            else:
                print_error("[ClanAPI] No clan found for tag: {}".format(clanTag))
                raise AsyncReturn(None)
        except AsyncReturn:
            raise
        except Exception as e:
            print_error("[ClanAPI] Error fetching clan ID for tag '{}': {}".format(clanTag, str(e)))
            raise AsyncReturn(None)

    def get_clan_id(self, clanTag, callback):
        @wg_async
        def worker():
            try:
                clanId = yield self._getClanIdAsync(clanTag)
                if clanId:
                    self.clanIdCache[clanTag] = clanId
                    BigWorld.callback(0.0, lambda: callback(clanTag, clanId))
                else:
                    if clanTag in self.clanIdCache:
                        print_debug("[ClanAPI] Using cached clan ID for '{}' (API failed)".format(clanTag))
                        BigWorld.callback(0.0, lambda: callback(clanTag, self.clanIdCache[clanTag]))
                    else:
                        BigWorld.callback(0.0, lambda: callback(clanTag, None))
            except Exception as e:
                print_error("[ClanAPI] Error in get_clan_id: {}".format(str(e)))
                # Try cache as fallback on exception
                if clanTag in self.clanIdCache:
                    print_debug("[ClanAPI] Using cached clan ID for '{}' (exception occurred)".format(clanTag))
                    BigWorld.callback(0.1, lambda: callback(clanTag, self.clanIdCache[clanTag]))
                else:
                    BigWorld.callback(0.1, lambda: callback(clanTag, None))

        worker()

    @wg_async
    def _getClanRatingAsync(self, clanId, battleLevel):
        if not clanId:
            print_debug("[ClanAPI] No clan_id provided")
            raise AsyncReturn(None)

        url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clanId)

        try:
            data = yield fetch_data_with_retry(url)

            if not data or 'stats' not in data:
                print_error("[ClanAPI] The 'stats' key or Data is missing from the API response.")
                raise AsyncReturn(None)

            if str(battleLevel) not in data['stats']:
                print_error("[ClanAPI] Data for level {} is missing from the API response.".format(battleLevel))
                raise AsyncReturn(None)

            eloRating = data['stats'][str(battleLevel)].get('elo', 0)
            print_debug("[ClanAPI] Clan rating for clan_id {} level {}: {}".format(clanId, battleLevel, eloRating))
            raise AsyncReturn(eloRating)

        except AsyncReturn:
            raise
        except Exception as e:
            print_error("[ClanAPI] Error fetching clan rating for clan_id {}: {}".format(clanId, str(e)))
            raise AsyncReturn(None)

    def get_clan_rating(self, clanId, battleLevel, guiType, callback):
        cacheKey = "{}_{}_{}".format(clanId, battleLevel, guiType)

        @wg_async
        def worker():
            try:
                rating = yield self._getClanRatingAsync(clanId, battleLevel)
                if rating is not None:
                    self.clanRatingCache[cacheKey] = rating
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, guiType, rating))
                else:
                    if cacheKey in self.clanRatingCache:
                        print_debug("[ClanAPI] Using cached rating for clan {} (API failed)".format(clanId))
                        BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, guiType, self.clanRatingCache[cacheKey]))
                    else:
                        BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, guiType, 0))
            except Exception as e:
                print_error("[ClanAPI] Error in get_clan_rating: {}".format(str(e)))
                if cacheKey in self.clanRatingCache:
                    print_debug("[ClanAPI] Using cached rating for clan {} (exception occurred)".format(clanId))
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, guiType, self.clanRatingCache[cacheKey]))
                else:
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, guiType, 0))

        worker()

    @wg_async
    def _getForLast28DaysAsync(self, clanId, battleLevel):
        if not clanId:
            print_debug("[ClanAPI] No clan_id provided")
            raise AsyncReturn(None)

        url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clanId)

        try:
            data = yield fetch_data_with_retry(url)

            if not data or 'stats' not in data:
                print_error("[ClanAPI] The 'stats' key or Data is missing from the API response.")
                raise AsyncReturn(None)

            if str(battleLevel) not in data['stats']:
                print_error("[ClanAPI] Data for level {} is missing from the API response.".format(battleLevel))
                raise AsyncReturn(None)

            winsPercent = data['stats'][str(battleLevel)]['sorties']['wins_percent_for_last_28_days']
            battlesCount = data['stats'][str(battleLevel)]['sorties']['battles_count_for_last_28_days']

            print_debug("[ClanAPI] 28-day stats for clan_id {} level {}: {}% wins, {} battles".format(
                clanId, battleLevel, winsPercent, battlesCount))
            raise AsyncReturn((winsPercent, battlesCount))

        except AsyncReturn:
            raise
        except Exception as e:
            print_error("[ClanAPI] Error fetching 28-day stats for clan_id {}: {}".format(clanId, str(e)))
            raise AsyncReturn(None)

    def get_for_last_28_days(self, clanId, battleLevel, callback):
        cacheKey = "stats_{}_{}".format(clanId, battleLevel)

        @wg_async
        def worker():
            try:
                result = yield self._getForLast28DaysAsync(clanId, battleLevel)
                if result is not None:
                    winsPercent, battlesCount = result
                    self.clanStatsCache[cacheKey] = (winsPercent, battlesCount)
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, winsPercent, battlesCount))
                else:
                    if cacheKey in self.clanStatsCache:
                        print_debug("[ClanAPI] Using cached stats for clan {} (API failed)".format(clanId))
                        winsPercent, battlesCount = self.clanStatsCache[cacheKey]
                        BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, winsPercent, battlesCount))
                    else:
                        BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, 0, 0))
            except Exception as e:
                print_error("[ClanAPI] Error in get_for_last_28_days: {}".format(str(e)))
                if cacheKey in self.clanStatsCache:
                    print_debug("[ClanAPI] Using cached stats for clan {} (exception occurred)".format(clanId))
                    winsPercent, battlesCount = self.clanStatsCache[cacheKey]
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, winsPercent, battlesCount))
                else:
                    BigWorld.callback(0.1, lambda: callback(clanId, battleLevel, 0, 0))

        worker()

    def clear_cache(self):
        self.clanIdCache.clear()
        self.clanRatingCache.clear()
        self.clanStatsCache.clear()
        print_debug("[ClanAPI] Cache cleared")

    def fini(self):
        self.clear_cache()
        print_debug("[ClanAPI] Finalized")
