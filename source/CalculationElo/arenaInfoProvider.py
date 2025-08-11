import BigWorld
from PlayerEvents import g_playerEvents
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from gui.mods.gambiter.flash import g_guiCache

from .config_param import g_configParams
from . import g_clanAPI, g_eloCalc, g_multiTextPanel
from .utils import print_log, print_error, print_debug


class ArenaInfoProvider(object):
    """Основний клас для збору та відображення інформації про арену"""
    
    __playerTeam = -1
    __guiType = -1
    __tank_tier = 10
    __arena = None

    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        print_debug("[ArenaInfoProvider] Initializing...")
        
        # Інформація про команди
        self.team_info = {
            'allies': None, 
            'enemies': None, 
            'id_allies': None, 
            'id_enemies': None,
            'allies_rating': None, 
            'enemies_rating': None,
            'elo_plus': None, 
            'elo_minus': None, 
            'wins_percent': None, 
            'battles_count': None
        }
        
        # Прапорець для відображення панелі
        self.ON_HOTKEY_PRESSED = False

        try:
            # Реєстрація обробників подій
            g_playerEvents.onAvatarReady += self.start
            g_playerEvents.onAvatarBecomeNonPlayer += self.stop
            self.sessionProvider.onBattleSessionStart += self.onBattleSessionStart
            self.sessionProvider.onBattleSessionStop += self.onBattleSessionStop
            print_debug("[ArenaInfoProvider] Event handlers registered successfully")
        except Exception as e:
            print_error("[ArenaInfoProvider] Error registering event handlers: %s" % str(e))

        print_debug("[ArenaInfoProvider] Initialization complete")

    def start(self, *a, **k):
        """Запуск провайдера при готовності аватара"""
        print_debug("[ArenaInfoProvider] Starting...")
        
        # Скидання інформації про команди
        self.team_info = {
            'allies': None, 
            'enemies': None, 
            'id_allies': None, 
            'id_enemies': None,
            'allies_rating': None, 
            'enemies_rating': None,
            'elo_plus': None, 
            'elo_minus': None, 
            'wins_percent': None, 
            'battles_count': None
        }
        
        def waitVehicles():
            """Очікування завантаження транспорту в арені"""
            try:
                print_debug("[ArenaInfoProvider] Waiting for vehicles...")
                
                # Перевірка режиму відображення
                display_mode = g_configParams.displayMode.value
                self.ON_HOTKEY_PRESSED = (display_mode == "always")
                print_debug("[ArenaInfoProvider] Display mode: %s, ON_HOTKEY_PRESSED: %s" % (display_mode, self.ON_HOTKEY_PRESSED))
                
                # Перевірка наявності транспорту
                vehicles = BigWorld.player().arena.vehicles.items()
                if len(vehicles) == 0:
                    print_debug("[ArenaInfoProvider] No vehicles found, retrying...")
                    BigWorld.callback(0.1, waitVehicles)
                    return

                print_debug("[ArenaInfoProvider] Found %d vehicles" % len(vehicles))
                    
                # Обробка тільки якщо мод увімкнений
                if g_configParams.enabled.value:
                    print_debug("[ArenaInfoProvider] Mod enabled, processing...")
                    
                    # Перевірка типу GUI (15-16 для Stronghold)
                    if self.__guiType in (15, 16):
                        print_debug("[ArenaInfoProvider] Valid GUI type: %d" % self.__guiType)
                        
                        # Отримання команди гравця
                        self.__playerTeam = BigWorld.player().team
                        print_debug("[ArenaInfoProvider] Player team: %d" % self.__playerTeam)

                        # Встановлення інформації про команди
                        self.set_team_info()
                        print_debug("[ArenaInfoProvider] Team info set - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
                        
                        # Отримання ID кланів
                        self.team_info['id_allies'] = g_clanAPI.get_clan_id(self.team_info['allies'])
                        self.team_info['id_enemies'] = g_clanAPI.get_clan_id(self.team_info['enemies'])
                        print_debug("[ArenaInfoProvider] Clan IDs - allies: %s, enemies: %s" % (self.team_info['id_allies'], self.team_info['id_enemies']))

                        # Отримання рівня танка гравця
                        self.__tank_tier = self.get_player_tank_tier(BigWorld.player().playerVehicleID)
                        print_debug("[ArenaInfoProvider] Player tank tier: %d" % self.__tank_tier)

                        # Отримання рейтингів кланів
                        self.team_info['allies_rating'] = g_clanAPI.get_clan_rating(self.team_info['id_allies'], self.__tank_tier, self.__guiType)
                        self.team_info['enemies_rating'] = g_clanAPI.get_clan_rating(self.team_info['id_enemies'], self.__tank_tier, self.__guiType)
                        print_debug("[ArenaInfoProvider] Ratings - allies: %s, enemies: %s" % (self.team_info['allies_rating'], self.team_info['enemies_rating']))
                        
                        # Розрахунок змін ELO
                        Elo = g_eloCalc.calculate_elo_changes(self.team_info['allies_rating'], self.team_info['enemies_rating'])
                        self.team_info['elo_plus'] = Elo[0]
                        self.team_info['elo_minus'] = Elo[1]
                        print_debug("[ArenaInfoProvider] ELO changes - plus: %s, minus: %s" % (self.team_info['elo_plus'], self.team_info['elo_minus']))

                        # Отримання статистики за 28 днів
                        self.team_info['wins_percent'], self.team_info['battles_count'] = g_clanAPI.get_for_last_28_days(self.team_info['id_enemies'], self.__tank_tier, self.__guiType)
                        print_debug("[ArenaInfoProvider] Last 28 days - wins percent: %s, battles count: %s" % (self.team_info['wins_percent'], self.team_info['battles_count']))
                        
                        # Оновлення існуючих компонентів (новий формат)
                        try:
                            # Перевірка для нової версії з allies_rating компонентом
                            if g_guiCache.isComponent('eloInfoPanel.alliesRating'):
                                print_debug("[ArenaInfoProvider] Updating existing text fields (new compact format)")
                                g_multiTextPanel.update_text_fields(
                                    self.team_info['allies'], 
                                    self.team_info['enemies'], 
                                    self.team_info['allies_rating'], 
                                    self.team_info['enemies_rating'], 
                                    self.team_info['elo_plus'], 
                                    self.team_info['elo_minus'], 
                                    self.team_info['wins_percent'], 
                                    self.team_info['battles_count']
                                )
                            else:
                                print_debug("[ArenaInfoProvider] Text fields not created yet")
                        except Exception as ex:
                            print_error("[ArenaInfoProvider] Error updating text fields: %s" % str(ex))
                    else:
                        print_debug("[ArenaInfoProvider] Invalid GUI type: %d" % self.__guiType)
                else:
                    print_debug("[ArenaInfoProvider] Mod disabled")
                    
            except Exception as e:
                print_error("[ArenaInfoProvider] Error in waitVehicles: %s" % str(e))
                
        # Запуск очікування транспорту
        waitVehicles()

    def stop(self, *a, **k):
        """Зупинка провайдера при виході з арени"""
        print_debug("[ArenaInfoProvider] Stopping...")
        
        # Скидання інформації про команди
        self.team_info = {
            'allies': None, 
            'enemies': None, 
            'id_allies': None, 
            'id_enemies': None,
            'allies_rating': None, 
            'enemies_rating': None,
            'elo_plus': None, 
            'elo_minus': None, 
            'wins_percent': None, 
            'battles_count': None
        }
        
        try:
            # Видалення всіх компонентів панелі
            g_multiTextPanel.delete_all_component()
            print_debug("[ArenaInfoProvider] Components deleted successfully")
        except Exception as ex:
            print_error('[ArenaInfoProvider] Error deleting components: %s' % str(ex))

    def onBattleSessionStart(self):
        """Обробник початку бойової сесії"""
        print_debug("[ArenaInfoProvider] Battle session started")

        try:
            # Отримання арени та типу GUI
            arena = BigWorld.player().arena
            self.__guiType = BigWorld.player().arena.guiType
            print_debug("[ArenaInfoProvider] GUI type: %d" % self.__guiType)
            
            # Визначення режиму відображення
            display_mode = g_configParams.displayMode.value
            self.ON_HOTKEY_PRESSED = (display_mode == "always")
            print_debug("[ArenaInfoProvider] Display mode: %s, always visible: %s" % (display_mode, self.ON_HOTKEY_PRESSED))
            
            # Запуск обробників клавіш
            g_multiTextPanel.start_key_held(self.ON_HOTKEY_PRESSED)
            
            # Пропускаємо sync_with_msa якщо g_config не ініціалізований
            try:
                from .config import g_config
                if g_config is not None:
                    g_config.sync_with_msa()
                else:
                    print_debug("[ArenaInfoProvider] Config not available, skipping sync")
            except Exception as e:
                print_debug("[ArenaInfoProvider] Could not sync config: %s" % str(e))

            # Створення компонентів тільки якщо мод увімкнений
            if g_configParams.enabled.value:
                print_debug("[ArenaInfoProvider] Mod enabled, checking GUI type...")
                
                if self.__guiType in (15, 16):
                    print_debug("[ArenaInfoProvider] Valid GUI type, creating text fields...")
                    
                    # Перевірка чи компоненти ще не створені (новий формат)
                    if not g_guiCache.isComponent('eloInfoPanel.alliesRating'):
                        print_debug("[ArenaInfoProvider] Creating text fields with visibility: %s" % self.ON_HOTKEY_PRESSED)
                        g_multiTextPanel.create_text_fields(
                            self.ON_HOTKEY_PRESSED, 
                            self.team_info['allies'], 
                            self.team_info['enemies'], 
                            self.team_info['allies_rating'], 
                            self.team_info['enemies_rating'], 
                            self.team_info['elo_plus'], 
                            self.team_info['elo_minus'],
                            self.team_info['wins_percent'],
                            self.team_info['battles_count']
                        )
                    else:
                        print_debug("[ArenaInfoProvider] Text fields already exist")
                else:
                    print_debug("[ArenaInfoProvider] Invalid GUI type: %d" % self.__guiType)
            else:
                print_debug("[ArenaInfoProvider] Mod disabled")
                
            self.__arena = arena
            
        except Exception as ex:
            print_error("[ArenaInfoProvider] Error in onBattleSessionStart: %s" % str(ex))

    def onBattleSessionStop(self):
        """Обробник завершення бойової сесії"""
        print_debug("[ArenaInfoProvider] Battle session stopped")
        
        try:
            arena = self.__arena
            
            # Зупинка обробників клавіш
            g_multiTextPanel.stop_key_held(self.ON_HOTKEY_PRESSED)
            print_debug("[ArenaInfoProvider] Key handlers stopped")

            if arena is None: 
                print_debug("[ArenaInfoProvider] Arena is None, skipping cleanup")
                return
            
            self.__arena = None
            print_debug("[ArenaInfoProvider] Arena reference cleared")
            
        except Exception as e:
            print_error("[ArenaInfoProvider] Error in onBattleSessionStop: %s" % str(e))

    def set_team_info(self):
        """Встановлення інформації про команди"""
        try:
            print_debug("[ArenaInfoProvider] Setting team info...")
            
            arena_dp = BigWorld.player().guiSessionProvider.getArenaDP()
            personal_description = arena_dp.getPersonalDescription()
            
            # Визначення союзників та ворогів залежно від команди гравця
            if self.__playerTeam == 2:
                self.team_info['allies'] = personal_description.getTeamName(2)
                self.team_info['enemies'] = personal_description.getTeamName(1)
                print_debug("[ArenaInfoProvider] Player on team 2 - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
            else: 
                self.team_info['allies'] = personal_description.getTeamName(1)
                self.team_info['enemies'] = personal_description.getTeamName(2)
                print_debug("[ArenaInfoProvider] Player on team 1 - allies: %s, enemies: %s" % (self.team_info['allies'], self.team_info['enemies']))
                
        except Exception as e:
            print_error("[ArenaInfoProvider] Error setting team info: %s" % str(e))
            # Встановлення значень за замовчуванням при помилці
            self.team_info['allies'] = "Unknown"
            self.team_info['enemies'] = "Unknown"

    def get_player_tank_tier(self, vehicle_id):
        """Отримання рівня танка гравця"""
        try:
            print_debug("[ArenaInfoProvider] Getting tank tier for vehicle ID: %s" % vehicle_id)
            
            vehicles = BigWorld.player().arena.vehicles
            if vehicle_id in vehicles:
                tier = vehicles[vehicle_id]['vehicleType'].level
                print_debug("[ArenaInfoProvider] Tank tier found: %d" % tier)
                return tier
            else:
                print_debug("[ArenaInfoProvider] Vehicle ID not found, using default tier 10")
                return 10
                
        except Exception as e:
            print_error("[ArenaInfoProvider] Error getting tank tier: %s" % str(e))
            return 10
    
    def fini(self):
        """Завершення роботи провайдера"""
        print_debug("[ArenaInfoProvider] Finalizing...")
        
        try:
            # Відключення обробників подій
            g_playerEvents.onAvatarReady -= self.start
            g_playerEvents.onAvatarBecomeNonPlayer -= self.stop
            self.sessionProvider.onBattleSessionStart -= self.onBattleSessionStart
            self.sessionProvider.onBattleSessionStop -= self.onBattleSessionStop
            print_debug("[ArenaInfoProvider] Event handlers unregistered successfully")
        except Exception as e:
            print_error("[ArenaInfoProvider] Error unregistering event handlers: %s" % str(e))
            
        print_debug("[ArenaInfoProvider] Finalization complete")