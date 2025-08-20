# -*- coding: utf-8 -*-
import os
import codecs
import threading
import BigWorld
from .utils import *
from .config_param import g_configParams


class AvgWN8:
    def __init__(self):
        self.history_wn8_path = os.path.join('mods', 'configs', 'under_pressure', 'CE_avgWN8.txt')
        self.wn8_cache = {} 

    def _ensure_config_directory(self):
        config_dir = os.path.dirname(self.history_wn8_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)


    
    def _get_recent_wn8_sync(self, account_id):
        url = "https://api.tomato.gg/dev/api-v2/player/recents/eu/{}?cache=false&battles=1000".format(account_id)
        
        try:
            data = fetch_data_with_retry(url)

            if not data or 'data' not in data:
                return 0
            if 'battles' not in data['data'] or '1000' not in data['data']['battles']:
                return 0
            if 'overall' not in data['data']['battles']['1000']:
                return 0
            if 'wn8' not in data['data']['battles']['1000']['overall']:
                return 0
            
            wn8_rating = data['data']['battles']['1000']['overall']['wn8']
            print_debug("WN8 fetched for account_id {}: {}".format(account_id, wn8_rating))
            return wn8_rating
                
        except Exception as e:
            print_error("Error while retrieving WN8 rating for account_id {}: {}".format(account_id, str(e)))
            return 0

    def get_wn8_async(self, account_id, callback):
        try:
            if account_id in self.wn8_cache:
                BigWorld.callback(0.0, lambda: callback(account_id, self.wn8_cache[account_id]))
                return
            
            def worker():
                wn8 = self._get_recent_wn8_sync(account_id)
                self.wn8_cache[account_id] = wn8
                BigWorld.callback(0.0, lambda: callback(account_id, wn8))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print_error("Error in get_wn8_async: {}".format(str(e)))
            BigWorld.callback(0.0, lambda: callback(account_id, 0))

    def get_avg_team_wn8(self, account_ids, final_callback):
        try:
            if not account_ids:
                BigWorld.callback(0.0, lambda: final_callback(0))
                return
            
            progress = {
                'total': len(account_ids),
                'completed': 0,
                'wn8_values': []
            }
            
            def individual_callback(account_id, wn8):
                try:
                    progress['completed'] += 1
                    if wn8 and wn8 > 0:
                        progress['wn8_values'].append(wn8)
                    
                    print_debug("WN8 progress: {}/{} (account_id: {}, wn8: {})".format(
                        progress['completed'], progress['total'], account_id, wn8))
                    
                    if progress['completed'] >= progress['total']:
                        if progress['wn8_values']:
                            avg_wn8 = int(round(sum(progress['wn8_values']) / len(progress['wn8_values'])))
                        else:
                            avg_wn8 = 0
                        
                        print_debug("Average team WN8 calculated: {}".format(avg_wn8))
                        final_callback(avg_wn8)
                        
                except Exception as e:
                    print_error("Error in individual callback: {}".format(str(e)))
            
            for account_id in account_ids:
                self.get_wn8_async(account_id, individual_callback)
            
            print_debug("Started async WN8 requests for {} accounts".format(len(account_ids)))
            
        except Exception as e:
            print_error("Error in get_avg_team_wn8: {}".format(str(e)))
            BigWorld.callback(0.0, lambda: final_callback(0))

    def clear_wn8_cache(self):
        self.wn8_cache.clear()
        print_debug("WN8 cache cleared")

    def save_team_wn8_history(self, avg_wn8, enemy_tag, enemy_rating):
        if not g_configParams.recordAvgTeamWn8.value or avg_wn8 == 0:
            return
        try:
            self._ensure_config_directory()
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            history_entry = "[{}] Enemy || Avg WN8: {} | TAG: {} | ELO: {} |\n".format(
                timestamp, int(avg_wn8), enemy_tag, enemy_rating
            )
            with codecs.open(self.history_wn8_path, 'a', encoding='utf-8') as f:
                f.write(history_entry)

            print_debug("Enemy Team WN8 history saved")

        except Exception as e:
            print_error("Error saving WN8 history: {}".format(str(e)))
    
    def clear_wn8_history(self):
        try:
            if os.path.exists(self.history_wn8_path):
                os.remove(self.history_wn8_path)
                print_debug("WN8 history file cleared successfully")
                return True
            return True         
        except Exception as e:
            print_error("Error clearing WN8 history: {}".format(str(e)))
            return False