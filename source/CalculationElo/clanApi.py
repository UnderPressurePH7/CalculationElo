# -*- coding: utf-8 -*-
import threading
import BigWorld
from .utils import *

class ClanAPI:
    
    def __init__(self):
        self.wg_key = '8f04db08e54ff45dbd7d4b7e7de0b76b'
        self.clan_id_cache = {}
        self.clan_rating_cache = {}
        self.clan_stats_cache = {}

    def _get_clan_id_sync(self, clan_tag):
        url = 'https://api.worldoftanks.eu/wot/clans/list/?application_id={}&search={}'.format(self.wg_key, clan_tag)
        
        try:
            data = fetch_data_with_retry(url)
            
            if data and data.get('status') == 'ok' and data.get('meta', {}).get('count', 0) > 0:
                clan_id = data['data'][0].get('clan_id')
                print_debug("Clan ID for tag '{}': {}".format(clan_tag, clan_id))
                return clan_id
            else:
                print_error("No clan found for tag: {}".format(clan_tag))
                return None
        except Exception as e:
            print_error("Error fetching clan ID for tag '{}': {}".format(clan_tag, str(e)))
            return None

    def get_clan_id(self, clan_tag, callback=None):
        if callback is None:
            if clan_tag in self.clan_id_cache:
                return self.clan_id_cache[clan_tag]
            
            clan_id = self._get_clan_id_sync(clan_tag)
            if clan_id:
                self.clan_id_cache[clan_tag] = clan_id
            return clan_id
        
        try:
            if clan_tag in self.clan_id_cache:
                BigWorld.callback(0.0, lambda: callback(clan_tag, self.clan_id_cache[clan_tag]))
                return
            
            def worker():
                clan_id = self._get_clan_id_sync(clan_tag)
                if clan_id:
                    self.clan_id_cache[clan_tag] = clan_id
                BigWorld.callback(0.0, lambda: callback(clan_tag, clan_id))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print_error("Error in get_clan_id async: {}".format(str(e)))
            BigWorld.callback(0.0, lambda: callback(clan_tag, None))

    def _get_clan_rating_sync(self, clan_id, battle_lvl, gui_type):
        if gui_type not in (15, 16):
            print_debug("Invalid GUI type: {}".format(gui_type))
            return 0
        
        if not clan_id:
            print_debug("No clan_id provided")
            return 0
            
        url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clan_id)
        
        try:
            data = fetch_data_with_retry(url)
            
            if not data or 'stats' not in data:
                print_error("The 'stats' key or Data is missing from the API response.")
                return 0

            if str(battle_lvl) not in data['stats']:
                print_error("Data for level {} is missing from the API response.".format(battle_lvl))
                return 0
            
            elo_rating = data['stats'][str(battle_lvl)]['elo']
            print_debug("Clan rating for clan_id {} level {}: {}".format(clan_id, battle_lvl, elo_rating))
            return elo_rating
            
        except Exception as e:
            print_error("Error fetching clan rating for clan_id {}: {}".format(clan_id, str(e)))
            return 0

    def get_clan_rating(self, clan_id, battle_lvl, gui_type, callback=None):
        cache_key = "{}_{}_{}".format(clan_id, battle_lvl, gui_type)
        
        if callback is None:
            if cache_key in self.clan_rating_cache:
                return self.clan_rating_cache[cache_key]
            
            rating = self._get_clan_rating_sync(clan_id, battle_lvl, gui_type)
            if rating:
                self.clan_rating_cache[cache_key] = rating
            return rating
        
        try:
            if cache_key in self.clan_rating_cache:
                BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, self.clan_rating_cache[cache_key]))
                return
            
            def worker():
                rating = self._get_clan_rating_sync(clan_id, battle_lvl, gui_type)
                if rating:
                    self.clan_rating_cache[cache_key] = rating
                BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, rating))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print_error("Error in get_clan_rating async: {}".format(str(e)))
            BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, 0))

    def _get_for_last_28_days_sync(self, clan_id, battle_lvl, gui_type):
        if gui_type not in (15, 16):
            print_debug("Invalid GUI type: {}".format(gui_type))
            return 0, 0
        
        if not clan_id:
            print_debug("No clan_id provided")
            return 0, 0
            
        url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clan_id)
        
        try:
            data = fetch_data_with_retry(url)
            
            if not data or 'stats' not in data:
                print_error("The 'stats' key or Data is missing from the API response.")
                return 0, 0

            if str(battle_lvl) not in data['stats']:
                print_error("Data for level {} is missing from the API response.".format(battle_lvl))
                return 0, 0
            
            wins_percent = data['stats'][str(battle_lvl)]['sorties']['wins_percent_for_last_28_days']
            battles_count = data['stats'][str(battle_lvl)]['sorties']['battles_count_for_last_28_days']
            
            print_debug("28-day stats for clan_id {} level {}: {}% wins, {} battles".format(
                clan_id, battle_lvl, wins_percent, battles_count))
            return wins_percent, battles_count
            
        except Exception as e:
            print_error("Error fetching 28-day stats for clan_id {}: {}".format(clan_id, str(e)))
            return 0, 0

    def get_for_last_28_days(self, clan_id, battle_lvl, gui_type, callback=None):
        cache_key = "stats_{}_{}_{}".format(clan_id, battle_lvl, gui_type)
        
        if callback is None:
            if cache_key in self.clan_stats_cache:
                return self.clan_stats_cache[cache_key]
            
            stats = self._get_for_last_28_days_sync(clan_id, battle_lvl, gui_type)
            if stats != (0, 0):
                self.clan_stats_cache[cache_key] = stats
            return stats

        try:
            if cache_key in self.clan_stats_cache:
                wins_percent, battles_count = self.clan_stats_cache[cache_key]
                BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, wins_percent, battles_count))
                return
            
            def worker():
                wins_percent, battles_count = self._get_for_last_28_days_sync(clan_id, battle_lvl, gui_type)
                if (wins_percent, battles_count) != (0, 0):
                    self.clan_stats_cache[cache_key] = (wins_percent, battles_count)
                BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, wins_percent, battles_count))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print_error("Error in get_for_last_28_days async: {}".format(str(e)))
            BigWorld.callback(0.0, lambda: callback(clan_id, battle_lvl, gui_type, 0, 0))

    def clear_cache(self):
        self.clan_id_cache.clear()
        self.clan_rating_cache.clear()
        self.clan_stats_cache.clear()
        print_debug("ClanAPI cache cleared")