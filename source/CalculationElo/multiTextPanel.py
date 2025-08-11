import BigWorld
import Keys
from gui import InputHandler
from gui.shared.utils.key_mapping import getBigworldNameFromKey

from gui.mods.gambiter import g_guiFlash, utils
from gui.mods.gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, g_guiCache

from .config_param import g_configParams
from .utils import print_log, print_error, print_debug
from . import *

class MultiTextPanel:

    utils.IS_DEBUG = False

    def __init__(self):
        print_debug("[MultiTextPanel] Initializing...")
        self.panel_id = 'eloInfoPanel'
        self.isKeyPressed = False
        self.active_keys = {}
        
        # Компактні розміри панелі
        self.panel_width = 80
        self.panel_height = 100
        
        # Позиція завантажується з конфігурації
        self.panel_x = 565
        self.panel_y = 50
        
        # Компоненти панелі
        self.components = {
            'background': '{}.background'.format(self.panel_id),
            'allies_rating': '{}.alliesRating'.format(self.panel_id),
            'enemies_rating': '{}.enemiesRating'.format(self.panel_id),
            'elo_plus': '{}.eloPlus'.format(self.panel_id),
            'elo_minus': '{}.eloMinus'.format(self.panel_id),
            'win_rate': '{}.winRate'.format(self.panel_id),
            'battles_count': '{}.battlesCount'.format(self.panel_id)
        }
        
        # Завантаження позиції з конфігурації
        self._load_position_from_config()
        
        try:
            initial_keys = g_configParams.eloHotKey.value
            if initial_keys and all(key > 0 for key in initial_keys):
                self.hot_keys = initial_keys
            else:
                print_debug("[MultiTextPanel] Invalid hot keys in config: %s, using default Alt" % str(initial_keys))
                self.hot_keys = [Keys.KEY_LALT]
            print_debug("[MultiTextPanel] Hot keys loaded: %s" % str(self.hot_keys))
        except Exception as e:
            print_error("[MultiTextPanel] Error loading hot keys: %s" % str(e))
            self.hot_keys = [Keys.KEY_LALT] 

        try:
            if not g_guiCache.isComponent(self.panel_id): 
                print_debug("[MultiTextPanel] Creating main panel component...")
                g_guiFlash.createComponent(self.panel_id, COMPONENT_TYPE.PANEL, {
                    'x': self.panel_x,
                    'y': self.panel_y,
                    'width': self.panel_width,
                    'height': self.panel_height,
                    'drag': True,
                    'border': False,  # Відключаємо стандартну рамку
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'visible': True
                })
                print_debug("[MultiTextPanel] Main panel created successfully")
            else:
                print_debug("[MultiTextPanel] Main panel already exists")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating main panel: %s" % str(e))
        
        print_debug("[MultiTextPanel] Initialization complete")

    def _load_position_from_config(self):
        """Завантаження тільки позиції з конфігурації (розмір фіксований)"""
        try:
            self.panel_x = g_configParams.panelX.value
            self.panel_y = g_configParams.panelY.value
            print_debug("[MultiTextPanel] Position loaded from config: (%d,%d)" % (self.panel_x, self.panel_y))
        except Exception as e:
            print_error("[MultiTextPanel] Error loading position from config: %s" % str(e))

    def _create_background(self):
        """Створення фонового компонента"""
        try:
            if not g_guiCache.isComponent(self.components['background']):
                print_debug("[MultiTextPanel] Creating background component...")
                
                alpha = g_configParams.panelAlpha.value
                show_border = g_configParams.showBorder.value
                
                g_guiFlash.createComponent(self.components['background'], COMPONENT_TYPE.SHAPE, {
                    'x': 0,
                    'y': 0,
                    'width': self.panel_width,
                    'height': self.panel_height,
                    'color': 0x000000,  # Чорний фон
                    'alpha': alpha,
                    'border': show_border,
                    'borderColor': 0x666666,  # Сірий кордон
                    'borderAlpha': 0.8,
                    'borderWidth': 1,  # Тонша рамка для компактності
                    'cornerRadius': 3  # Менші заокруглені кути
                })
                print_debug("[MultiTextPanel] Background created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating background: %s" % str(e))

    def _create_allies_components(self):
        """Створення компонента для рейтингу союзників"""
        try:
            allies_color = self._get_allies_color()
            
            # Тільки рейтинг союзників (без лейбла для економії місця)
            if not g_guiCache.isComponent(self.components['allies_rating']):
                allies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>----</b></font>'.format(allies_color)
                g_guiFlash.createComponent(self.components['allies_rating'], COMPONENT_TYPE.LABEL, {
                    'text': allies_rating_text,
                    'x': 3,
                    'y': 5,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'shadow': self._get_text_shadow()
                })
                
            print_debug("[MultiTextPanel] Allies component created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating allies component: %s" % str(e))

    def _create_enemies_components(self):
        """Створення компонента для рейтингу ворогів"""
        try:
            enemies_color = self._get_enemies_color()
            
            # Тільки рейтинг ворогів (без лейбла для економії місця)
            if not g_guiCache.isComponent(self.components['enemies_rating']):
                enemies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>----</b></font>'.format(enemies_color)
                g_guiFlash.createComponent(self.components['enemies_rating'], COMPONENT_TYPE.LABEL, {
                    'text': enemies_rating_text,
                    'x': self.panel_width - 3,
                    'y': 5,
                    'alignX': COMPONENT_ALIGN.RIGHT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'shadow': self._get_text_shadow()
                })
                
            print_debug("[MultiTextPanel] Enemies component created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating enemies component: %s" % str(e))

    def _create_elo_components(self):
        """Створення компонентів для ELO"""
        try:
            additional_color = self._get_additional_color()
            
            # ELO + (ліва сторона)
            if not g_guiCache.isComponent(self.components['elo_plus']):
                elo_plus_text = '<font face="Tahoma" size="14" color="{0}"><b>+0</b></font>'.format(additional_color)
                g_guiFlash.createComponent(self.components['elo_plus'], COMPONENT_TYPE.LABEL, {
                    'text': elo_plus_text,
                    'x': 3,
                    'y': 30,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'visible': self._get_elo_visible(),
                    'shadow': self._get_text_shadow()
                })
            
            # ELO - (права сторона)
            if not g_guiCache.isComponent(self.components['elo_minus']):
                elo_minus_text = '<font face="Tahoma" size="14" color="{0}"><b>-0</b></font>'.format(additional_color)
                g_guiFlash.createComponent(self.components['elo_minus'], COMPONENT_TYPE.LABEL, {
                    'text': elo_minus_text,
                    'x': self.panel_width - 3,
                    'y': 30,
                    'alignX': COMPONENT_ALIGN.RIGHT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'visible': self._get_elo_visible(),
                    'shadow': self._get_text_shadow()
                })
                
            print_debug("[MultiTextPanel] ELO components created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating ELO components: %s" % str(e))

    def _create_stats_components(self):
        """Створення компонентів для статистики за 28 днів"""
        try:
            additional_color = self._get_additional_color()
            
            # Процент побід (ліва сторона)
            if not g_guiCache.isComponent(self.components['win_rate']):
                win_rate_text = '<font face="Tahoma" size="12" color="{0}"><b>0%</b></font>'.format(additional_color)
                g_guiFlash.createComponent(self.components['win_rate'], COMPONENT_TYPE.LABEL, {
                    'text': win_rate_text,
                    'x': 3,
                    'y': 55,
                    'alignX': COMPONENT_ALIGN.LEFT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'visible': self._get_enemies_for_28_days_visible(),
                    'shadow': self._get_text_shadow()
                })
            
            # Кількість боїв (права сторона)
            if not g_guiCache.isComponent(self.components['battles_count']):
                battles_text = '<font face="Tahoma" size="12" color="{0}"><b>0</b></font>'.format(additional_color)
                g_guiFlash.createComponent(self.components['battles_count'], COMPONENT_TYPE.LABEL, {
                    'text': battles_text,
                    'x': self.panel_width - 3,
                    'y': 55,
                    'alignX': COMPONENT_ALIGN.RIGHT,
                    'alignY': COMPONENT_ALIGN.TOP,
                    'isHtml': True,
                    'autoSize': True,
                    'visible': self._get_enemies_for_28_days_visible(),
                    'shadow': self._get_text_shadow()
                })
                
            print_debug("[MultiTextPanel] Stats components created successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error creating stats components: %s" % str(e))

    def _get_text_shadow(self):
        """Повертає стандартні налаштування тіні для тексту"""
        return {
            'distance': 1,
            'angle': 45,
            'color': 0x000000,
            'alpha': 0.8,
            'blurX': 1,  # Менша тінь для компактності
            'blurY': 1,
            'strength': 1,
            'quality': 1
        }

    def _get_allies_color(self):
        try:
            color = g_configParams.alliesColor.value
            if isinstance(color, (list, tuple)) and len(color) == 3:
                return "#%02X%02X%02X" % (int(color[0]), int(color[1]), int(color[2]))
            return "#00FF00"  # Зелений за замовчуванням
        except Exception as e:
            print_error("[MultiTextPanel] Error getting allies color: %s" % str(e))
            return "#00FF00"

    def _get_enemies_color(self):
        try:
            color = g_configParams.enemiesColor.value
            if isinstance(color, (list, tuple)) and len(color) == 3:
                return "#%02X%02X%02X" % (int(color[0]), int(color[1]), int(color[2]))
            return "#FF0000"  # Червоний за замовчуванням
        except Exception as e:
            print_error("[MultiTextPanel] Error getting enemies color: %s" % str(e))
            return "#FF0000"

    def _get_additional_color(self):
        try:
            color = g_configParams.additionalColor.value
            if isinstance(color, (list, tuple)) and len(color) == 3:
                return "#%02X%02X%02X" % (int(color[0]), int(color[1]), int(color[2]))
            return "#FFFFFF"  # Білий за замовчуванням
        except Exception as e:
            print_error("[MultiTextPanel] Error getting additional color: %s" % str(e))
            return "#FFFFFF"

    def _get_elo_visible(self):
        try:
            return g_configParams.eloVisible.value
        except Exception as e:
            print_error("[MultiTextPanel] Error getting eloVisible: %s" % str(e))
            return True

    def _get_enemies_for_28_days_visible(self):
        try:
            return g_configParams.enemiesFor28DaysVisible.value
        except Exception as e:
            print_error("[MultiTextPanel] Error getting enemiesFor28DaysVisible: %s" % str(e))
            return True

    def create_text_fields(self, elo_visible, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count):
        """Створення всіх компонентів панелі"""
        print_debug("[MultiTextPanel] Creating text fields - visible: %s, allies: %s, enemies: %s" % (elo_visible, allies, enemies))
        
        try:
            # Встановлення видимості головної панелі
            g_guiFlash.updateComponent(self.panel_id, {'visible': elo_visible})
            print_debug("[MultiTextPanel] Panel visibility set to: %s" % elo_visible)
            
            # Перевірка чи компоненти вже існують
            if g_guiCache.isComponent(self.components['background']):
                print_debug("[MultiTextPanel] Components already exist, updating instead of creating")
                self.update_text_fields(allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count)
                return

            # Створення всіх компонентів по порядку
            self._create_background()
            self._create_allies_components()
            self._create_enemies_components()
            self._create_elo_components()
            self._create_stats_components()
            
            # Оновлення з початковими даними
            self.update_text_fields(allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count)
            
            print_debug("[MultiTextPanel] All components created successfully")
            
        except Exception as e:
            print_error("[MultiTextPanel] Error creating text fields: %s" % str(e))

    def update_text_fields(self, allies, enemies, allies_rating, enemies_rating, eloPlus, eloMinus, wins_percent, battles_count):
        """Оновлення всіх текстових полів"""
        print_debug("[MultiTextPanel] Updating text fields - allies: %s, enemies: %s" % (allies, enemies))
        
        try:
            allies_color = self._get_allies_color()
            enemies_color = self._get_enemies_color()
            additional_color = self._get_additional_color()

            # Оновлення лейбла союзників
            allies_label_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(
                allies_color, allies or "ALLIES"
            )
            if g_guiCache.isComponent(self.components['allies_label']):
                g_guiFlash.updateComponent(self.components['allies_label'], {'text': allies_label_text})

            # Оновлення рейтингу союзників
            allies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(
                allies_color, allies_rating or "----"
            )
            if g_guiCache.isComponent(self.components['allies_rating']):
                g_guiFlash.updateComponent(self.components['allies_rating'], {'text': allies_rating_text})

            # Оновлення лейбла ворогів
            enemies_label_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(
                enemies_color, enemies or "ENEMIES"
            )
            if g_guiCache.isComponent(self.components['enemies_label']):
                g_guiFlash.updateComponent(self.components['enemies_label'], {'text': enemies_label_text})

            # Оновлення рейтингу ворогів
            enemies_rating_text = '<font face="Tahoma" size="18" color="{0}"><b>{1}</b></font>'.format(
                enemies_color, enemies_rating or "----"
            )
            if g_guiCache.isComponent(self.components['enemies_rating']):
                g_guiFlash.updateComponent(self.components['enemies_rating'], {'text': enemies_rating_text})

            # Оновлення ELO
            if self._get_elo_visible():
                elo_plus_text = '<font face="Tahoma" size="14" color="{0}"><b>+{1}</b></font>'.format(
                    additional_color, eloPlus or "0"
                )
                elo_minus_text = '<font face="Tahoma" size="14" color="{0}"><b>{1}</b></font>'.format(
                    additional_color, eloMinus or "0"
                )
                
                if g_guiCache.isComponent(self.components['elo_plus']):
                    g_guiFlash.updateComponent(self.components['elo_plus'], {
                        'text': elo_plus_text,
                        'visible': True
                    })
                if g_guiCache.isComponent(self.components['elo_minus']):
                    g_guiFlash.updateComponent(self.components['elo_minus'], {
                        'text': elo_minus_text,
                        'visible': True
                    })

            # Оновлення статистики за 28 днів
            if self._get_enemies_for_28_days_visible():
                win_rate_text = '<font face="Tahoma" size="12" color="{0}"><b>{1}%</b></font>'.format(
                    additional_color, wins_percent or "0"
                )
                # Скорочено текст боїв (тільки число)
                battles_text = '<font face="Tahoma" size="12" color="{0}"><b>{1}</b></font>'.format(
                    additional_color, battles_count or "0"
                )
                
                if g_guiCache.isComponent(self.components['win_rate']):
                    g_guiFlash.updateComponent(self.components['win_rate'], {
                        'text': win_rate_text,
                        'visible': True
                    })
                if g_guiCache.isComponent(self.components['battles_count']):
                    g_guiFlash.updateComponent(self.components['battles_count'], {
                        'text': battles_text,
                        'visible': True
                    })
            
            print_debug("[MultiTextPanel] Text fields updated successfully")
            
        except Exception as e:
            print_error("[MultiTextPanel] Error updating text fields: %s" % str(e))

    def update_panel_settings(self):
        """Оновлення налаштувань панелі з конфігурації (тільки позиція)"""
        try:
            print_debug("[MultiTextPanel] Updating panel settings from config...")
            
            # Оновлення тільки позиції
            new_x = g_configParams.panelX.value
            new_y = g_configParams.panelY.value
            
            if new_x != self.panel_x or new_y != self.panel_y:
                self.panel_x = new_x
                self.panel_y = new_y
                
                # Оновлення головної панелі
                if g_guiCache.isComponent(self.panel_id):
                    g_guiFlash.updateComponent(self.panel_id, {
                        'x': self.panel_x,
                        'y': self.panel_y
                    })
                
                print_debug("[MultiTextPanel] Panel position updated")
            
            # Оновлення прозорості та рамки
            if g_guiCache.isComponent(self.components['background']):
                g_guiFlash.updateComponent(self.components['background'], {
                    'alpha': g_configParams.panelAlpha.value,
                    'border': g_configParams.showBorder.value
                })
            
            # Оновлення видимості компонентів
            self._update_component_visibility()
            
        except Exception as e:
            print_error("[MultiTextPanel] Error updating panel settings: %s" % str(e))

    def _update_component_visibility(self):
        """Оновлення видимості компонентів згідно з конфігурацією"""
        try:
            elo_visible = self._get_elo_visible()
            stats_visible = self._get_enemies_for_28_days_visible()
            
            # Оновлення видимості ELO компонентів
            for component_name in ['elo_plus', 'elo_minus']:
                component_id = self.components[component_name]
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.updateComponent(component_id, {'visible': elo_visible})
            
            # Оновлення видимості статистики
            for component_name in ['win_rate', 'battles_count']:
                component_id = self.components[component_name]
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.updateComponent(component_id, {'visible': stats_visible})
            
            print_debug("[MultiTextPanel] Component visibility updated")
            
        except Exception as e:
            print_error("[MultiTextPanel] Error updating component visibility: %s" % str(e))

    def update_panel_position_from_drag(self, x, y):
        """Оновлення позиції панелі після перетягування"""
        try:
            self.panel_x = x
            self.panel_y = y
            
            g_configParams.panelX.value = x
            g_configParams.panelY.value = y
            
            try:
                from .config import g_config
                if g_config:
                    g_config.save_config()
            except Exception as e:
                print_debug("[MultiTextPanel] Could not save position to config: %s" % str(e))
            
            print_debug("[MultiTextPanel] Panel position updated from drag: %d, %d" % (x, y))
            
        except Exception as e:
            print_error("[MultiTextPanel] Error updating panel position from drag: %s" % str(e))

    def delete_all_component(self):
        """Видалення всіх компонентів панелі"""
        print_debug("[MultiTextPanel] Deleting all components")
        
        # Видалення в зворотному порядку створення
        components_to_delete = [
            self.components['battles_count'],
            self.components['win_rate'],
            self.components['elo_minus'],
            self.components['elo_plus'],
            self.components['enemies_rating'],
            self.components['allies_rating'],
            self.components['background']
        ]
        
        for component_id in components_to_delete:
            try:
                if g_guiCache.isComponent(component_id):
                    g_guiFlash.deleteComponent(component_id)
                    print_debug("[MultiTextPanel] Component deleted: %s" % component_id)
            except Exception as e:
                print_error("[MultiTextPanel] Error deleting component %s: %s" % (component_id, str(e)))

    def update_hotkeys(self):
        try:
            old_keys = self.hot_keys
            new_keys = g_configParams.eloHotKey.value
            
            if new_keys and all(key > 0 for key in new_keys):
                self.hot_keys = new_keys
                if old_keys != self.hot_keys:
                    print_debug("[MultiTextPanel] Hot keys updated: %s -> %s" % (str(old_keys), str(self.hot_keys)))
            else:
                print_debug("[MultiTextPanel] Invalid hot keys, keeping current: %s" % str(self.hot_keys))
                
        except Exception as e:
            print_error("[MultiTextPanel] Error updating hot keys: %s" % str(e))

    def check_keyset(self, keyset):
        """Перевірка чи натиснуті всі клавіші з набору"""
        if not keyset or len(keyset) == 0:
            return False
        return all(self.active_keys.get(key, False) for key in keyset)

    def start_key_held(self, elo_visible):
        """Запуск обробки натискання клавіш"""
        print_debug("[MultiTextPanel] Starting key event handlers - elo_visible: %s" % elo_visible)
        
        if elo_visible:
            print_debug("[MultiTextPanel] ELO always visible, skipping key handlers")
            return
            
        try:
            print_debug("[MultiTextPanel] Registering key event handlers...")
            InputHandler.g_instance.onKeyDown += self.onKeyDown
            InputHandler.g_instance.onKeyUp += self.onKeyUp
            print_debug("[MultiTextPanel] Key event handlers registered successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error registering key handlers: %s" % str(e))
    
    def stop_key_held(self, elo_visible):
        """Зупинка обробки натискання клавіш"""
        print_debug("[MultiTextPanel] Stopping key event handlers - elo_visible: %s" % elo_visible)
        
        if elo_visible:
            print_debug("[MultiTextPanel] ELO always visible, skipping key handler removal")
            return
            
        try:
            print_debug("[MultiTextPanel] Unregistering key event handlers...")
            InputHandler.g_instance.onKeyDown -= self.onKeyDown
            InputHandler.g_instance.onKeyUp -= self.onKeyUp
            print_debug("[MultiTextPanel] Key event handlers unregistered successfully")
        except Exception as e:
            print_error("[MultiTextPanel] Error unregistering key handlers: %s" % str(e))

    def onKeyDown(self, event):
        """Обробка натискання клавіші"""
        try:
            key_name = getBigworldNameFromKey(event.key) if hasattr(event, 'key') else 'Unknown'
            print_debug("[MultiTextPanel] Key down: %s (%s)" % (key_name, event.key))
            
            self.active_keys[event.key] = True
            
            if self.check_keyset(self.hot_keys):
                print_debug("[MultiTextPanel] Hotkey combination pressed, starting key hold")
                self.isKeyPressed = True
                BigWorld.callback(0.1, self.onKeyHold)
            else:
                print_debug("[MultiTextPanel] Hotkey combination not pressed")
                
        except Exception as e:
            print_error("[MultiTextPanel] Error in onKeyDown: %s" % str(e))

    def onKeyUp(self, event):
        """Обробка відпускання клавіші"""
        try:
            key_name = getBigworldNameFromKey(event.key) if hasattr(event, 'key') else 'Unknown'
            print_debug("[MultiTextPanel] Key up: %s (%s)" % (key_name, event.key))
            
            if event.key in self.active_keys:
                self.active_keys[event.key] = False
                
            if event.key in self.hot_keys:
                print_debug("[MultiTextPanel] Hotkey released, stopping key hold")
                self.isKeyPressed = False
                
        except Exception as e:
            print_error("[MultiTextPanel] Error in onKeyUp: %s" % str(e))

    def onKeyHold(self):
        """Обробка утримування клавіші"""
        try:
            if self.isKeyPressed and self.check_keyset(self.hot_keys):
                if g_guiCache.isComponent(self.panel_id):
                    g_guiFlash.updateComponent(self.panel_id, {'visible': True})
                BigWorld.callback(0.1, self.onKeyHold)
            else:
                if g_guiCache.isComponent(self.panel_id):
                    g_guiFlash.updateComponent(self.panel_id, {'visible': False})
                
        except Exception as e:
            print_error("[MultiTextPanel] Error in onKeyHold: %s" % str(e))