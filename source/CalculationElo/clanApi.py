# -*- coding: utf-8 -*-
from .utils import *

class ClanAPI:
    
    def __init__(self):
        self.wg_key = '8f04db08e54ff45dbd7d4b7e7de0b76b'


    def get_clan_id(self, clan_tag):

        url  = 'https://api.worldoftanks.eu/wot/clans/list/?application_id={}&search={}'.format(self.wg_key, clan_tag)

        data = fetch_data_with_retry(url)

        if data and data.get('status') == 'ok' and data.get('meta', {}).get('count', 0) > 0:
            clan_id = data['data'][0].get('clan_id')
            print_debug("Clan ID for tag '{}': {}".format(clan_tag, clan_id))
            return clan_id
        else:
            print_error("No clan found for tag: {}".format(clan_tag))
        return None
 

    def get_clan_rating(self, clan_id, batle_lvl, gui_type):
        if gui_type in (15, 16):
            url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clan_id)
            data = fetch_data_with_retry(url)    
            if not data or 'stats' not in data:
                print_error("The 'stats' key or Data is missing from the API response.")
                return 0

            if str(batle_lvl) not in data['stats']:
                print_error("Data for level {} is missing from the API response.".format(batle_lvl))
                return 0
            
            elo_rating = data['stats'][str(batle_lvl)]['elo']
            return elo_rating
        

    def get_for_last_28_days(self, clan_id, batle_lvl, gui_type):

        if gui_type in (15, 16):
            url = "https://wgsh-woteu.wargaming.net/game_api/stronghold_info/clan/{}".format(clan_id)
            data = fetch_data_with_retry(url)    
            if not data or 'stats' not in data:
                print_error("The 'stats' key or Data is missing from the API response.")
                return 0

            if str(batle_lvl) not in data['stats']:
                print_error("Data for level {} is missing from the API response.".format(batle_lvl))
                return 0
            
            wins_percent = data['stats'][str(batle_lvl)]['sorties']['wins_percent_for_last_28_days']
            battles_count = data['stats'][str(batle_lvl)]['sorties']['battles_count_for_last_28_days']
            return wins_percent, battles_count        

