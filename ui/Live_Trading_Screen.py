# live_trading_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty, DictProperty, StringProperty
from kivy.clock import Clock, mainthread
from kivy.utils import get_color_from_hex
from Backend.database import DatabaseManager
from utils import hex_to_rgb
import json

def get_all_strategies():
    db = DatabaseManager()
    return db.get_all_strategies()

class OrdersScreen(Screen):
    symbol = StringProperty('')
    strategy_name = StringProperty('')
    strategy_params = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = None
        self.header_label = None
        self.orders_layout = None
        self.build_ui()

    def build_ui(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        with self.main_layout.canvas.before:
            Color(*hex_to_rgb('#f0f4f7'))
            self.main_rect = RoundedRectangle(pos=self.main_layout.pos, size=self.main_layout.size, radius=[10])
        self.main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Initially create a placeholder label for header
        self.header_label = Label(
            text="Loading strategy details...",
            font_size='16sp',
            color=get_color_from_hex('#2c3e50'),
            halign='left',
            valign='middle'
        )
        self.main_layout.add_widget(self.header_label)

        # Orders section
        self.orders_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.orders_layout.bind(minimum_height=self.orders_layout.setter('height'))
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.orders_layout)

        self.orders_layout.add_widget(Label(
            text="(No orders yet, will update in real-time)",
            color=get_color_from_hex('#7f8c8d'), font_size='14sp'
        ))

        self.main_layout.add_widget(scroll_view)

        # Buttons
        buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1,0.1), spacing=10)
        terminate_button = Button(
            text="Terminate Strategy",
            background_normal='',
            background_color=get_color_from_hex('#e74c3c'),
            color=get_color_from_hex('#ffffff'),
            bold=True, font_size='16sp'
        )
        terminate_button.bind(on_release=self.terminate_strategy)

        leave_button = Button(
            text="Leave Running",
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True, font_size='16sp'
        )
        leave_button.bind(on_release=self.leave_running)

        buttons_layout.add_widget(terminate_button)
        buttons_layout.add_widget(leave_button)
        self.main_layout.add_widget(buttons_layout)

        self.add_widget(self.main_layout)

    def on_pre_enter(self, *args):
        # Update header now that symbol, strategy_name, and strategy_params are set
        interval = self.strategy_params.get('interval', '?')
        filtered_params = {k:v for k,v in self.strategy_params.items() if k not in ['symbol','interval','strategy_class_name','start_date','end_date']}
        params_str = ", ".join([f"{k}={v}" for k,v in filtered_params.items()]) or "No extra params"

        symbol_display = self.symbol if self.symbol else "?"
        strategy_display = self.strategy_name if self.strategy_name else "?"

        header_text = f"Strategy: {strategy_display}, Symbol: {symbol_display}, Interval: {interval}, Params: {params_str}"
        self.header_label.text = header_text

    def update_main_rect(self, instance, value):
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def terminate_strategy(self, instance):
        self.manager.get_screen('live_trading').set_strategy_status(self.strategy_name, False)
        self.manager.current = 'live_trading'

    def leave_running(self, instance):
        # Just go back, do not change running status
        self.manager.current = 'live_trading'

class LiveTradingScreen(Screen):
    running_strategies = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = None
        self.scroll_box = None
        self.build_ui()

    def build_ui(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        with self.main_layout.canvas.before:
            Color(*hex_to_rgb('#f0f4f7'))
            self.main_rect = RoundedRectangle(pos=self.main_layout.pos, size=self.main_layout.size, radius=[10])
        self.main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        header_label = Label(
            text="Live Trading Screen",
            font_size='28sp',
            bold=True,
            color=get_color_from_hex('#34495e')
        )
        self.main_layout.add_widget(header_label)

        self.strategies_layout = GridLayout(cols=1, spacing=10, size_hint=(1,0.8))
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.scroll_box = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.scroll_box.bind(minimum_height=self.scroll_box.setter('height'))
        self.scroll_view.add_widget(self.scroll_box)
        self.strategies_layout.add_widget(self.scroll_view)
        self.main_layout.add_widget(self.strategies_layout)

        bottom_layout = BoxLayout(orientation='horizontal', size_hint=(1,0.1), spacing=10)
        refresh_button = Button(
            text="Refresh",
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),
            color=get_color_from_hex('#ffffff'),
            bold=True, font_size='18sp'
        )
        refresh_button.bind(on_release=lambda x: self.update_strategies())
        bottom_layout.add_widget(refresh_button)

        back_button = Button(
            text="Back to Dashboard",
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True, font_size='18sp'
        )
        back_button.bind(on_release=lambda x: setattr(self.manager, 'current', 'dashboard'))
        bottom_layout.add_widget(back_button)

        self.main_layout.add_widget(bottom_layout)
        self.add_widget(self.main_layout)

    def on_enter(self, *args):
        # Refresh strategies each time we enter, so status updates appear
        self.update_strategies()

    def update_main_rect(self, instance, value):
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def update_strategies(self):
        self.scroll_box.clear_widgets()

        strategies = get_all_strategies()
        if not strategies:
            self.scroll_box.add_widget(Label(text="No saved strategies.", font_size='16sp', color=get_color_from_hex('#7f8c8d')))
            return

        for s in strategies:
            self.add_strategy_item(s)

    def add_strategy_item(self, strategy):
        parameters_json = strategy['parameters']
        try:
            loaded_params = json.loads(parameters_json)
        except json.JSONDecodeError:
            loaded_params = {}

        item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=10)
        with item_layout.canvas.before:
            Color(*hex_to_rgb('#ffffff'))
            rect = RoundedRectangle(pos=item_layout.pos, size=item_layout.size, radius=[10])
        item_layout.bind(pos=lambda instance, value: setattr(rect, 'pos', instance.pos),
                         size=lambda instance, value: setattr(rect, 'size', instance.size))

        name_label = Label(
            text=strategy['name'],
            font_size='16sp',
            color=get_color_from_hex('#2c3e50'),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        name_label.size_hint_x = 0.4

        symbol_input = TextInput(
            hint_text="Symbol to run",
            multiline=False,
            size_hint=(0.3, 1),
            background_normal='',
            background_color=get_color_from_hex('#bdc3c7'),
            foreground_color=get_color_from_hex('#2c3e50'),
            font_size='14sp'
        )

        running = self.running_strategies.get(strategy['name'], False)
        status_text = "Running" if running else "Not Running"
        status_label = Label(
            text=status_text,
            font_size='14sp',
            color=get_color_from_hex('#34495e'),
            halign='center',
            valign='middle',
            size_hint=(0.2, 1)
        )
        status_label.bind(size=status_label.setter('text_size'))

        # Button(s) depending on running state
        buttons_layout = BoxLayout(orientation='horizontal', size_hint=(0.3, 1), spacing=5)

        if running:
            # If running, show Terminate and View buttons
            terminate_button = Button(
                text='Terminate',
                background_normal='',
                background_color=get_color_from_hex('#e74c3c'),
                color=get_color_from_hex('#ffffff'),
                bold=True,
                font_size='14sp',
                size_hint=(0.5, 1)
            )
            terminate_button.bind(on_release=lambda x: self.terminate_running_strategy(strategy['name']))

            view_button = Button(
                text='View',
                background_normal='',
                background_color=get_color_from_hex('#2980b9'),
                color=get_color_from_hex('#ffffff'),
                bold=True,
                font_size='14sp',
                size_hint=(0.5, 1)
            )
            view_button.bind(on_release=lambda x: self.view_orders_screen(strategy, loaded_params))

            buttons_layout.add_widget(terminate_button)
            buttons_layout.add_widget(view_button)

        else:
            # If not running, show Run button
            run_button = Button(
                text='Run',
                background_normal='',
                background_color=get_color_from_hex('#27ae60'),
                color=get_color_from_hex('#ffffff'),
                bold=True,
                font_size='14sp',
                size_hint=(1, 1)
            )
            run_button.bind(on_release=lambda x: self.run_strategy(strategy, symbol_input.text.strip()))
            buttons_layout.add_widget(run_button)

        item_layout.add_widget(name_label)
        item_layout.add_widget(symbol_input)
        item_layout.add_widget(status_label)
        item_layout.add_widget(buttons_layout)

        self.scroll_box.add_widget(item_layout)

    def terminate_running_strategy(self, strategy_name):
        self.set_strategy_status(strategy_name, False)
        self.update_strategies()

    def view_orders_screen(self, strategy, parameters):
        # Assuming symbol is in parameters
        symbol = parameters.get('symbol', '?')
        if 'strategy_class_name' not in parameters:
            self.display_error_message("Strategy missing strategy_class_name.")
            return

        # Already running, so presumably symbol and interval are set
        orders_screen = self.manager.get_screen('orders')
        orders_screen.symbol = symbol
        orders_screen.strategy_name = strategy['name']
        orders_screen.strategy_params = parameters
        self.manager.current = 'orders'

    def run_strategy(self, strategy, symbol):
        if not symbol:
            self.display_error_message("Please enter a symbol before running.")
            return

        parameters = json.loads(strategy['parameters'])
        if 'strategy_class_name' not in parameters:
            self.display_error_message("Saved strategy missing strategy_class_name.")
            return

        parameters['symbol'] = symbol
        parameters['start_date'] = None
        parameters['end_date'] = None

        self.running_strategies[strategy['name']] = True

        orders_screen = self.manager.get_screen('orders')
        orders_screen.symbol = symbol
        orders_screen.strategy_name = strategy['name']
        orders_screen.strategy_params = parameters
        self.manager.current = 'orders'

    def set_strategy_status(self, strategy_name, running: bool):
        self.running_strategies[strategy_name] = running
        # After setting status, update the strategies to refresh status label
        self.update_strategies()

    @mainthread
    def display_error_message(self, message):
        error_label = Label(
            text=message,
            font_size='16sp',
            color=get_color_from_hex('#e74c3c'),
            size_hint=(1, None),
            height=40
        )
        self.main_layout.add_widget(error_label)
        Clock.schedule_once(lambda dt: self.remove_error_message(error_label), 3)

    @mainthread
    def remove_error_message(self, label):
        if label in self.main_layout.children:
            self.main_layout.remove_widget(label)