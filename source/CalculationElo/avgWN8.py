# -*- coding: utf-8 -*-
from .utils import *


class AvgWN8:

    def get_recent_wn8(self, account_id):

        url = "https://api.tomato.gg/dev/api-v2/player/recents/eu/{}?cache=false&battles=1000".format(account_id)
        
        try:
            data = fetch_data_with_retry(url)
            
            if not data:
                print_error("Failed to retrieve data from API.")
                return 0
            if 'data' not in data:
                print_error("Key 'data' is missing in the API response.")
                return 0

            if 'battles' not in data['data']:
                print_error("Key 'battles' is missing in the API response.")
                return 0
            
            if '1000' not in data['data']['battles']:
                print_error("Data for 1000 battles is missing in the API response.")
                return 0
            
            battles_data = data['data']['battles']['1000']
            if 'overall' not in battles_data:
                print_error("Overall statistics ('overall') are missing in the API response.")
                return 0

            overall_stats = battles_data['overall']
            if 'wn8' not in overall_stats:
                print_error("WN8 rating not found in the API response.")
                return 0
            
            wn8_rating = overall_stats['wn8']
            return wn8_rating
                
        except Exception as e:
            print_error("Error while retrieving WN8 rating: {}".format(str(e)))
            return 0
        
    def get_avg_team_wn8(self, wn8, count):
        if count == 0:
            return 0
        for wn8_value in wn8:
            wn8 += wn8_value
        return wn8 / count
