# ui/strategies_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, DictProperty
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from ui.custom_widgets import StrategyItem
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from Backend.backtester import backtest_strategy
from Backend.Strategies import MovingAverageCrossoverStrategy, RsiStrategy, BollingerBandsStrategy
import threading
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
from utils import hex_to_rgb  # Ensure utils.py is properly defined

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategiesScreen(Screen):
    api_manager = ObjectProperty(None)
    selected_strategy = StringProperty('Moving Average Crossover')  # Default strategy
    strategy_params = DictProperty({})  # To store strategy parameters

    def __init__(self, api_manager, **kwargs):
        super().__init__(**kwargs)
        self.api_manager = api_manager
        self.db = self.api_manager.db  # Assuming DatabaseManager is accessible
        self.build_ui()

    def build_ui(self):
        # Main Layout
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Set Background Color for main_layout
        with self.main_layout.canvas.before:
            Color(*hex_to_rgb('#f0f4f7'))  # Light grayish-blue background
            self.main_rect = RoundedRectangle(pos=self.main_layout.pos, size=self.main_layout.size, radius=[10])
        self.main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Header
        header = BoxLayout(size_hint=(1, 0.1), padding=(0, 10), spacing=10)
        header_label = Label(
            text="📚 Strategies",
            font_size='28sp',
            bold=True,
            color=get_color_from_hex('#34495e')
        )
        header.add_widget(header_label)
        self.main_layout.add_widget(header)

        # Strategy Selection Layout
        self.strategy_selection_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)

        self.strategy_spinner = Spinner(
            text=self.selected_strategy,  # Set default text
            values=('Moving Average Crossover', 'RSI Strategy', 'Bollinger Bands Strategy'),
            size_hint=(0.5, 1),  # Increased size_hint_x to 0.5
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),  # Blue
            color=get_color_from_hex('#ffffff'),
            bold=True,  # Spinner supports bold via font properties if customized
            font_size='18sp'
        )
        self.strategy_spinner.bind(text=self.on_strategy_select)

        # Optional: Wrap spinner in a container with fixed width
        spinner_container = BoxLayout(size_hint=(None, 1), width=250)  # Adjust width as needed
        spinner_container.add_widget(self.strategy_spinner)

        self.strategy_selection_layout.add_widget(Label(
            text='Strategy:',
            font_size='18sp',
            color=get_color_from_hex('#34495e'),
            halign='right',
            valign='middle'
        ))
        self.strategy_selection_layout.add_widget(spinner_container)  # Use container instead of spinner directly

        self.main_layout.add_widget(self.strategy_selection_layout)

        # General Parameters Layout
        self.general_params_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), spacing=10)

        # Symbol Input
        self.symbol_input = TextInput(
            text='AAPL',
            multiline=False,
            size_hint=(0.5, 1),
            background_normal='',
            background_color=get_color_from_hex('#bdc3c7'),
            foreground_color=get_color_from_hex('#2c3e50'),  # Corrected property
            font_size='16sp'
        )
        self.start_date_input = TextInput(
            text='2015-01-01',
            multiline=False,
            size_hint=(1, 1),
            background_normal='',
            background_color=get_color_from_hex('#bdc3c7'),
            foreground_color=get_color_from_hex('#2c3e50'),
            font_size='16sp'
        )
        self.end_date_input = TextInput(
            text='2020-01-01',
            multiline=False,
            size_hint=(1, 1),
            background_normal='',
            background_color=get_color_from_hex('#bdc3c7'),
            foreground_color=get_color_from_hex('#2c3e50'),
            font_size='16sp'
        )
        self.interval_input = TextInput(
            text='1d',
            multiline=False,
            size_hint=(0.3, 1),
            background_normal='',
            background_color=get_color_from_hex('#bdc3c7'),
            foreground_color=get_color_from_hex('#2c3e50'),
            font_size='16sp'
        )

        # Add widgets to general_params_layout
        self.general_params_layout.add_widget(Label(
            text='Symbol:',
            font_size='16sp',
            color=get_color_from_hex('#34495e'),
            halign='right',
            valign='middle'
        ))
        self.general_params_layout.add_widget(self.symbol_input)

        self.general_params_layout.add_widget(Label(
            text='Start Date:',
            font_size='16sp',
            color=get_color_from_hex('#34495e'),
            halign='right',
            valign='middle'
        ))
        self.general_params_layout.add_widget(self.start_date_input)

        self.general_params_layout.add_widget(Label(
            text='End Date:',
            font_size='16sp',
            color=get_color_from_hex('#34495e'),
            halign='right',
            valign='middle'
        ))
        self.general_params_layout.add_widget(self.end_date_input)

        self.general_params_layout.add_widget(Label(
            text='Interval:',
            font_size='16sp',
            color=get_color_from_hex('#34495e'),
            halign='right',
            valign='middle'
        ))
        self.general_params_layout.add_widget(self.interval_input)

        self.main_layout.add_widget(self.general_params_layout)

        # Strategy Parameters Layout
        self.params_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=10, padding=(20, 0))
        self.main_layout.add_widget(self.params_layout)

        # Initialize with default strategy parameters
        self.display_strategy_params(self.selected_strategy)

        # Strategies List
        self.strategies_list_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.4), spacing=10)
        self.main_layout.add_widget(self.strategies_list_layout)

        self.update_strategies()

        # Navigation Buttons
        self.navigation_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)

        back_button = Button(
            text="Back to Dashboard",
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),  # Blue
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        back_button.bind(on_release=self.go_to_dashboard)

        backtest_button = Button(
            text="Go to Backtest",
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),  # Green
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        backtest_button.bind(on_release=self.go_to_backtest)

        # Wrap buttons in containers with fixed width
        back_button_container = BoxLayout(size_hint=(None, 1), width=200)  # Adjust width as needed
        back_button_container.add_widget(back_button)

        backtest_button_container = BoxLayout(size_hint=(None, 1), width=200)  # Adjust width as needed
        backtest_button_container.add_widget(backtest_button)

        self.navigation_buttons_layout.add_widget(back_button_container)
        self.navigation_buttons_layout.add_widget(backtest_button_container)

        self.main_layout.add_widget(self.navigation_buttons_layout)

        # Add main layout to the screen
        self.add_widget(self.main_layout)

    def update_main_rect(self, instance, value):
        """Updates the main_layout background rectangle."""
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def create_output_box(self, title, value):
        """
        Creates a styled output box with a title and a value label.
        """
        box = BoxLayout(orientation='vertical', size_hint=(0.25, 1), padding=10)

        # Create the background rectangle and store its reference in the box
        with box.canvas.before:
            Color(*hex_to_rgb('#ecf0f1'))  # Light background
            output_bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[10])
        box.output_bg = output_bg  # Attach the reference to the box

        # Bind the update_output_bg method to position and size changes
        box.bind(pos=self.update_output_bg, size=self.update_output_bg)

        # Title Label
        title_label = Label(
            text=title,
            font_size='16sp',
            bold=True,
            color=get_color_from_hex('#34495e'),
            halign='center',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))

        # Value Label
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
        """
        Updates the background's position and size for output boxes.
        """
        instance.output_bg.pos = instance.pos
        instance.output_bg.size = instance.size

    def on_strategy_select(self, spinner, text):
        self.selected_strategy = text
        self.display_strategy_params(text)

    def display_strategy_params(self, strategy_name):
        """
        Displays parameter input fields based on the selected strategy.
        """
        self.params_layout.clear_widgets()
        self.strategy_params = {}  # Reset parameters

        if strategy_name == 'Moving Average Crossover':
            # Create input fields for Moving Average Crossover parameters
            short_input = TextInput(
                text='50',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),  # Corrected property
                font_size='16sp'
            )
            long_input = TextInput(
                text='200',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )

            # Add to params_layout
            param_box1 = BoxLayout(orientation='horizontal', spacing=10)
            param_box1.add_widget(Label(
                text='Short MA Period:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box1.add_widget(short_input)

            param_box2 = BoxLayout(orientation='horizontal', spacing=10)
            param_box2.add_widget(Label(
                text='Long MA Period:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box2.add_widget(long_input)

            self.params_layout.add_widget(param_box1)
            self.params_layout.add_widget(param_box2)

            # Store references to input fields
            self.strategy_params = {
                'short_period': short_input,
                'long_period': long_input,
            }

        elif strategy_name == 'RSI Strategy':
            # Create input fields for RSI parameters
            rsi_period_input = TextInput(
                text='14',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )
            rsi_overbought_input = TextInput(
                text='70',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )
            rsi_oversold_input = TextInput(
                text='30',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )

            # Add to params_layout
            param_box1 = BoxLayout(orientation='horizontal', spacing=10)
            param_box1.add_widget(Label(
                text='RSI Period:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box1.add_widget(rsi_period_input)

            param_box2 = BoxLayout(orientation='horizontal', spacing=10)
            param_box2.add_widget(Label(
                text='RSI Overbought:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box2.add_widget(rsi_overbought_input)

            param_box3 = BoxLayout(orientation='horizontal', spacing=10)
            param_box3.add_widget(Label(
                text='RSI Oversold:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box3.add_widget(rsi_oversold_input)

            self.params_layout.add_widget(param_box1)
            self.params_layout.add_widget(param_box2)
            self.params_layout.add_widget(param_box3)

            # Store references to input fields
            self.strategy_params = {
                'rsi_period': rsi_period_input,
                'rsi_upper': rsi_overbought_input,
                'rsi_lower': rsi_oversold_input,
            }

        elif strategy_name == 'Bollinger Bands Strategy':
            # Create input fields for Bollinger Bands parameters
            period_input = TextInput(
                text='20',
                multiline=False,
                input_filter='int',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )
            devfactor_input = TextInput(
                text='2',
                multiline=False,
                input_filter='float',
                size_hint=(0.3, 1),
                background_normal='',
                background_color=get_color_from_hex('#bdc3c7'),
                foreground_color=get_color_from_hex('#2c3e50'),
                font_size='16sp'
            )

            # Add to params_layout
            param_box1 = BoxLayout(orientation='horizontal', spacing=10)
            param_box1.add_widget(Label(
                text='Bollinger Period:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box1.add_widget(period_input)

            param_box2 = BoxLayout(orientation='horizontal', spacing=10)
            param_box2.add_widget(Label(
                text='Deviation Factor:',
                font_size='16sp',
                color=get_color_from_hex('#34495e'),
                halign='right',
                valign='middle'
            ))
            param_box2.add_widget(devfactor_input)

            self.params_layout.add_widget(param_box1)
            self.params_layout.add_widget(param_box2)

            # Store references to input fields
            self.strategy_params = {
                'period': period_input,
                'devfactor': devfactor_input,
            }

        else:
            # Handle unknown strategy
            self.params_layout.add_widget(Label(
                text="Unknown strategy selected.",
                color=get_color_from_hex('#e74c3c'),
                font_size='16sp'
            ))

    def update_strategies(self):
        """
        Updates the list of strategies displayed.
        """
        self.strategies_list_layout.clear_widgets()
        try:
            strategies = self.db.get_all_strategies()
            if strategies:
                for strategy in strategies:
                    item = StrategyItem(strategy=strategy)
                    self.strategies_list_layout.add_widget(item)
            else:
                self.strategies_list_layout.add_widget(Label(
                    text="No strategies available.",
                    font_size='18sp',
                    color=get_color_from_hex('#7f8c8d')
                ))
        except Exception as e:
            logger.error(f"Error fetching strategies: {e}")
            self.strategies_list_layout.add_widget(Label(
                text="Error fetching strategies.",
                font_size='18sp',
                color=get_color_from_hex('#e74c3c')
            ))

    def go_to_dashboard(self, instance):
        self.manager.current = 'dashboard'

    def go_to_backtest(self, instance):
        """
        Collects the selected strategy and its parameters, then navigates to the BacktestScreen.
        """
        selected_strategy = self.selected_strategy
        params = {}

        # Collect strategy-specific parameters
        if selected_strategy == 'RSI Strategy':
            try:
                params['rsi_period'] = int(self.strategy_params['rsi_period'].text)
                params['rsi_upper'] = int(self.strategy_params['rsi_upper'].text)
                params['rsi_lower'] = int(self.strategy_params['rsi_lower'].text)
            except ValueError:
                # Handle invalid input
                logger.error("Invalid RSI parameters.")
                self.display_error_message("Invalid RSI parameters. Please enter valid integers.")
                return
        elif selected_strategy == 'Bollinger Bands Strategy':
            try:
                params['period'] = int(self.strategy_params['period'].text)
                params['devfactor'] = float(self.strategy_params['devfactor'].text)
            except ValueError:
                # Handle invalid input
                logger.error("Invalid Bollinger Bands parameters.")
                self.display_error_message("Invalid Bollinger Bands parameters. Please enter valid numbers.")
                return
        elif selected_strategy == 'Moving Average Crossover':
            try:
                params['short_period'] = int(self.strategy_params['short_period'].text)
                params['long_period'] = int(self.strategy_params['long_period'].text)
            except ValueError:
                # Handle invalid input
                logger.error("Invalid Moving Average Crossover parameters.")
                self.display_error_message("Invalid Moving Average Crossover parameters. Please enter valid integers.")
                return
        else:
            # Handle unknown strategy
            logger.error("Unknown strategy selected.")
            self.display_error_message("Unknown strategy selected.")
            return

        # Collect general parameters
        symbol = self.symbol_input.text.strip().upper()
        start_date = self.start_date_input.text.strip()
        end_date = self.end_date_input.text.strip()
        interval = self.interval_input.text.strip()

        # Basic validation
        if not symbol:
            self.display_error_message("Symbol cannot be empty.")
            return
        if not self.validate_date(start_date):
            self.display_error_message("Invalid start date format. Use YYYY-MM-DD.")
            return
        if not self.validate_date(end_date):
            self.display_error_message("Invalid end date format. Use YYYY-MM-DD.")
            return
        if interval not in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']:
            self.display_error_message("Invalid interval. Choose from supported intervals.")
            return

        # Aggregate all parameters
        all_params = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval
        }
        all_params.update(params)  # Add strategy-specific params

        # Pass the selected strategy and parameters to BacktestScreen
        backtest_screen = self.manager.get_screen('backtest')
        backtest_screen.set_strategy(selected_strategy, all_params)

        # Navigate to BacktestScreen
        self.manager.current = 'backtest'

    def validate_date(self, date_str):
        """
        Validates the date format YYYY-MM-DD.
        """
        from datetime import datetime
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @mainthread
    def display_error_message(self, message):
        """
        Displays an error message to the user.
        """
        error_label = Label(
            text=message,
            font_size='16sp',
            color=get_color_from_hex('#e74c3c'),
            size_hint=(1, None),
            height=40
        )
        self.main_layout.add_widget(error_label)
        Clock.schedule_once(lambda dt: self.remove_error_message(error_label), 3)  # Remove after 3 seconds

    @mainthread
    def remove_error_message(self, label):
        self.main_layout.remove_widget(label)
