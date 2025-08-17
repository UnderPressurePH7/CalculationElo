# -*- coding: utf-8 -*-
import os
import codecs
from .utils import *
from .config_param import g_configParams


class AvgWN8:
    def __init__(self):
        self.history_wn8_path = os.path.join('mods', 'configs', 'under_pressure', 'CE_avgWN8.txt')

    def _ensure_config_directory(self):
        config_dir = os.path.dirname(self.history_wn8_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def _get_recent_wn8(self, account_id):

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
        
    def get_avg_team_wn8(self, account_ids):
        wn8_values = []
        for account_id in account_ids:
            wn8 = self._get_recent_wn8(account_id)
            wn8_values.append(wn8)
        if not wn8_values:  
            return 0
        avgTeamWN8 = round(sum(wn8_values) / len(wn8_values), 0)
        return int(avgTeamWN8)


    def save_team_wn8_history(self, avg_wn8):
        if not g_configParams.recordAvgTeamWn8.value:
            return
        try:
            self._ensure_config_directory()
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            history_entry = "[{}] Avg Enemy WN8: {} |\n".format(
                timestamp,
                int(avg_wn8)
            )
            with codecs.open(self.history_wn8_path, 'a', encoding='utf-8') as f:
                f.write(history_entry)

            print_debug("Enemy Team WN8 history saved to: {}".format(self.history_wn8_path))

        except Exception as e:
            print_error("Error saving WN8 history: {}".format(str(e)))
    
    def clear_wn8_history(self):
        try:
            if os.path.exists(self.history_wn8_path):
                os.remove(self.history_wn8_path)
                print_debug("WN8 history file cleared successfully")
                return True
            else:
                print_debug("WN8 history file does not exist")
                return True         
        except Exception as e:
            print_error("Error clearing WN8 history: %s" % str(e))