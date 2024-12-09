# ui/backtesting_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
from kivy_garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import logging
import json
import uuid

from utils import hex_to_rgb
from Backend.Strategies import (MovingAverageCrossoverStrategy, RsiStrategy,
                                BollingerBandsStrategy, MACDStrategy,
                                MeanReversionStrategy, BreakoutStrategy)
from Backend.backtester import backtest_strategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestScreen(Screen):
    api_manager = ObjectProperty(None)
    selected_strategy = StringProperty('')
    strategy_params = DictProperty({})
    current_strategy_label = None  # label to show current strategy details at top

    def __init__(self, api_manager, **kwargs):
        super().__init__(**kwargs)
        self.api_manager = api_manager
        self.db = self.api_manager.db
        self.build_ui()
        self.populate_saved_strategies()

    def build_ui(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        with self.main_layout.canvas.before:
            Color(*hex_to_rgb('#f0f4f7'))
            self.main_rect = RoundedRectangle(pos=self.main_layout.pos, size=self.main_layout.size, radius=[10])
        self.main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Header showing current strategy and params
        self.current_strategy_label = Label(
            text="No strategy running.",
            font_size='16sp',
            color=get_color_from_hex('#2c3e50'),
            halign='left',
            valign='middle',
            size_hint=(1, 0.05)
        )
        self.main_layout.add_widget(self.current_strategy_label)

        # Outputs layout
        self.outputs_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        self.sharpe_box = self.create_output_box('Sharpe Ratio', 'N/A')
        self.initial_box = self.create_output_box('Initial Portfolio', 'N/A')
        self.final_box = self.create_output_box('Final Portfolio', 'N/A')
        self.trades_box = self.create_output_box('Number of Trades', 'N/A')
        self.outputs_layout.add_widget(self.sharpe_box)
        self.outputs_layout.add_widget(self.initial_box)
        self.outputs_layout.add_widget(self.final_box)
        self.outputs_layout.add_widget(self.trades_box)
        self.main_layout.add_widget(self.outputs_layout)

        # Run Backtest Button
        self.run_backtest_button = Button(
            text="Run Backtest",
            size_hint=(1, 0.05),
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        self.run_backtest_button.bind(on_release=self.run_backtest)
        self.main_layout.add_widget(self.run_backtest_button)

        # Plot layout
        self.plot_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6), spacing=10, padding=(0, 10))
        self.plot_placeholder = Label(
            text="No backtest run yet.",
            font_size='18sp',
            color=get_color_from_hex('#7f8c8d')
        )
        self.plot_layout.add_widget(self.plot_placeholder)
        self.main_layout.add_widget(self.plot_layout)

        # Save/Load Layout
        save_load_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        self.save_strategy_button = Button(
            text="Save Strategy",
            size_hint=(0.2, 1),
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        self.save_strategy_button.bind(on_release=self.save_current_strategy)
        save_load_layout.add_widget(self.save_strategy_button)

        self.saved_strategies_spinner = Spinner(
            text='Select Saved Strategy',
            values=(),
            size_hint=(0.3, 1)
        )
        save_load_layout.add_widget(self.saved_strategies_spinner)

        input_layout = BoxLayout(orientation='vertical', size_hint=(0.3, 1), spacing=5)
        self.symbol_input = TextInput(hint_text="Symbol", multiline=False)
        self.start_date_input = TextInput(hint_text="Start Date (YYYY-MM-DD)", multiline=False)
        self.end_date_input = TextInput(hint_text="End Date (YYYY-MM-DD)", multiline=False)
        input_layout.add_widget(self.symbol_input)
        input_layout.add_widget(self.start_date_input)
        input_layout.add_widget(self.end_date_input)

        save_load_layout.add_widget(input_layout)

        self.run_saved_button = Button(
            text="Run Saved Strategy",
            size_hint=(0.2, 1),
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        self.run_saved_button.bind(on_release=self.run_selected_saved_strategy)
        save_load_layout.add_widget(self.run_saved_button)

        self.main_layout.add_widget(save_load_layout)

        # Navigation Buttons
        self.navigation_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=10)
        strategies_button = Button(
            text="Strategies",
            size_hint=(0.4, 1),
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        strategies_button.bind(on_release=self.go_to_strategies)

        dashboard_button = Button(
            text="Dashboard",
            size_hint=(0.4, 1),
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        dashboard_button.bind(on_release=self.go_to_dashboard)

        strategies_container = BoxLayout(size_hint=(None, 1), width=200)
        strategies_container.add_widget(strategies_button)

        dashboard_container = BoxLayout(size_hint=(None, 1), width=200)
        dashboard_container.add_widget(dashboard_button)

        self.navigation_buttons_layout.add_widget(strategies_container)
        self.navigation_buttons_layout.add_widget(dashboard_container)
        self.main_layout.add_widget(self.navigation_buttons_layout)

        self.add_widget(self.main_layout)

    def create_output_box(self, title, value):
        box = BoxLayout(orientation='vertical', size_hint=(0.25, 1), padding=10)
        with box.canvas.before:
            Color(*hex_to_rgb('#ecf0f1'))
            output_bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[10])
        box.output_bg = output_bg
        box.bind(pos=self.update_output_bg, size=self.update_output_bg)

        title_label = Label(
            text=title,
            font_size='16sp',
            bold=True,
            color=get_color_from_hex('#34495e'),
            halign='center',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))

        value_label = Label(
            text=value,
            font_size='18sp',
            color=get_color_from_hex('#2c3e50'),
            halign='center',
            valign='middle'
        )
        value_label.bind(size=value_label.setter('text_size'))

        box.add_widget(title_label)
        box.add_widget(value_label)
        return box

    def update_output_bg(self, instance, value):
        instance.output_bg.pos = instance.pos
        instance.output_bg.size = instance.size

    def update_main_rect(self, instance, value):
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def go_to_strategies(self, instance):
        self.manager.current = 'strategies'

    def go_to_dashboard(self, instance):
        self.manager.current = 'dashboard'

    def set_strategy(self, strategy_name, params):
        # We now trust that strategy_class_name is part of params, or must be set by the caller
        # If not present, error:
        if 'strategy_class_name' not in params:
            self.display_error_message("No strategy_class_name specified in params.")
            return
        self.selected_strategy = strategy_name
        self.strategy_params = params

    def run_backtest(self, instance):
        logger.info(f"Running backtest for strategy: {self.selected_strategy} with params: {self.strategy_params}")
        symbol = self.strategy_params.get('symbol')
        start_date = self.strategy_params.get('start_date')
        end_date = self.strategy_params.get('end_date')
        interval = self.strategy_params.get('interval')
        strategy_class_name = self.strategy_params.get('strategy_class_name')

        if not strategy_class_name:
            self.display_error_message("No strategy_class_name in parameters.")
            return

        strategy_map = {
            'MovingAverageCrossoverStrategy': MovingAverageCrossoverStrategy,
            'RsiStrategy': RsiStrategy,
            'BollingerBandsStrategy': BollingerBandsStrategy,
            'MACDStrategy': MACDStrategy,
            'MeanReversionStrategy': MeanReversionStrategy,
            'BreakoutStrategy': BreakoutStrategy
        }

        strategy_class = strategy_map.get(strategy_class_name)
        if not strategy_class:
            self.display_error_message(f"Strategy class {strategy_class_name} not supported.")
            return

        # Remove keys not for the strategy init
        strategy_specific_params = {k: v for k, v in self.strategy_params.items() if
                                    k not in ['symbol', 'start_date', 'end_date', 'interval', 'strategy_class_name']}

        try:
            fig, sharpe_ratio, num_trades, initial_portfolio, final_portfolio = backtest_strategy(
                strategy_class=strategy_class,
                ticker=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                **strategy_specific_params
            )
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            self.display_error_message(f"Backtest failed: {str(e)}")
            return

        if self.plot_placeholder in self.plot_layout.children:
            self.plot_layout.remove_widget(self.plot_placeholder)

        self.plot_layout.clear_widgets()
        if fig:
            self.graph_plot = FigureCanvasKivyAgg(fig)
            self.plot_layout.add_widget(self.graph_plot)
            plt.close(fig)
        else:
            self.plot_layout.add_widget(Label(text="No plot available."))

        # Update outputs
        try:
            self.sharpe_box.children[0].text = f"{sharpe_ratio:.2f}"
            self.initial_box.children[0].text = f"${initial_portfolio:.2f}"
            self.final_box.children[0].text = f"${final_portfolio:.2f}"
            self.trades_box.children[0].text = f"{num_trades}"
        except Exception as e:
            logger.error(f"Error updating output boxes: {e}")
            self.display_error_message("Error updating output boxes.")

        # Update the top label with currently running strategy details
        param_str = ", ".join([f"{k}={v}" for k,v in strategy_specific_params.items()])
        self.current_strategy_label.text = f"Running {strategy_class_name} on {symbol} ({interval}) with params: {param_str}"

    def on_leave(self):
        # Clear spinner and inputs
        self.saved_strategies_spinner.values = ()
        self.saved_strategies_spinner.text = 'Select Saved Strategy'
        self.symbol_input.text = ''
        self.start_date_input.text = ''
        self.end_date_input.text = ''
        self.plot_layout.clear_widgets()
        # Reset the top label
        self.current_strategy_label.text = "No strategy running."

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

    def save_current_strategy(self, instance):
        if not self.selected_strategy or not self.strategy_params:
            self.display_error_message("No strategy or parameters selected.")
            return

        # Ensure strategy_class_name is present
        if 'strategy_class_name' not in self.strategy_params:
            self.display_error_message("No strategy_class_name in parameters.")
            return

        # Remove symbol, start_date, end_date only
        filtered_params = {k: v for k, v in self.strategy_params.items()
                           if k not in ['symbol', 'start_date', 'end_date']}

        strategy_id = str(uuid.uuid4())
        name = self.generate_strategy_name(self.selected_strategy, filtered_params)
        description = f"Auto-saved strategy: {name}"
        parameters_json = json.dumps(filtered_params)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (strategy_id, name, description, parameters)
            VALUES (?, ?, ?, ?)
        """, (strategy_id, name, description, parameters_json))
        self.db.conn.commit()
        self.display_error_message("Strategy saved successfully.")
        self.populate_saved_strategies()

    def generate_strategy_name(self, strategy_name, params):
        strategy_class_name = params.get('strategy_class_name', '')
        interval = params.get('interval', 'unknown')
        # Check which strategy_class_name and pick out main params:
        if strategy_class_name == 'MovingAverageCrossoverStrategy':
            short_p = params.get('short_period', '?')
            long_p = params.get('long_period', '?')
            name = f"MAC: {short_p}, {long_p} (int={interval})"
        elif strategy_class_name == 'RsiStrategy':
            rsi_period = params.get('rsi_period', '?')
            rsi_upper = params.get('rsi_upper', '?')
            rsi_lower = params.get('rsi_lower', '?')
            name = f"RSI: p={rsi_period}, U={rsi_upper}, L={rsi_lower} (int={interval})"
        elif strategy_class_name == 'BollingerBandsStrategy':
            period = params.get('period', '?')
            devfactor = params.get('devfactor', '?')
            name = f"BB: p={period}, d={devfactor} (int={interval})"
        elif strategy_class_name == 'MACDStrategy':
            fast = params.get('fast_period', '?')
            slow = params.get('slow_period', '?')
            signal = params.get('signal_period', '?')
            name = f"MACD: f={fast}, s={slow}, sig={signal} (int={interval})"
        elif strategy_class_name == 'MeanReversionStrategy':
            lookback = params.get('lookback_period', '?')
            threshold = params.get('threshold', '?')
            name = f"MR: lb={lookback}, thr={threshold} (int={interval})"
        elif strategy_class_name == 'BreakoutStrategy':
            lookback = params.get('lookback_period', '?')
            factor = params.get('breakout_factor', '?')
            name = f"BO: lb={lookback}, f={factor} (int={interval})"
        else:
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            name = f"{strategy_name}: {param_str}"

        return name

    def populate_saved_strategies(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT strategy_id, name FROM strategies")
        rows = cursor.fetchall()

        self.saved_strategies = {row[1]: row[0] for row in rows}
        self.saved_strategies_spinner.values = list(self.saved_strategies.keys()) if self.saved_strategies else ()

    def run_selected_saved_strategy(self, instance):
        selected_name = self.saved_strategies_spinner.text
        if selected_name == 'Select Saved Strategy' or selected_name not in self.saved_strategies:
            self.display_error_message("No saved strategy selected.")
            return

        strategy_id = self.saved_strategies[selected_name]
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT parameters FROM strategies WHERE strategy_id = ?", (strategy_id,))
        row = cursor.fetchone()
        if not row:
            self.display_error_message("Strategy not found in database.")
            return

        parameters_json = row[0]
        try:
            loaded_params = json.loads(parameters_json)
        except json.JSONDecodeError:
            self.display_error_message("Error loading strategy parameters.")
            return

        symbol = self.symbol_input.text.strip()
        start_date = self.start_date_input.text.strip()
        end_date = self.end_date_input.text.strip()

        if not symbol or not start_date or not end_date:
            self.display_error_message("Please provide symbol, start date, and end date.")
            return

        interval = loaded_params.get('interval')
        if not interval:
            self.display_error_message("Saved strategy does not have an interval specified.")
            return

        strategy_class_name = loaded_params.get('strategy_class_name')
        if not strategy_class_name:
            self.display_error_message("Saved strategy does not have a strategy_class_name specified.")
            return

        loaded_params['symbol'] = symbol
        loaded_params['start_date'] = start_date
        loaded_params['end_date'] = end_date
        loaded_params['interval'] = interval

        self.selected_strategy = selected_name
        self.strategy_params = loaded_params

        self.run_backtest(None)

    def on_enter(self):
        self.populate_saved_strategies()
        self.symbol_input.text = ''
        self.start_date_input.text = ''
        self.end_date_input.text = ''
        self.sharpe_box.children[0].text = 'N/A'
        self.initial_box.children[0].text = 'N/A'
        self.final_box.children[0].text = 'N/A'
        self.trades_box.children[0].text = 'N/A'