# ui/backtesting_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
from kivy_garden.matplotlib import FigureCanvasKivyAgg  # Ensure kivy_garden.matplotlib is installed
from utils import hex_to_rgb  # Ensure utils.py is properly defined
import matplotlib.pyplot as plt
import logging

# Import Strategy Classes
from Backend.Strategies import MovingAverageCrossoverStrategy, RsiStrategy, BollingerBandsStrategy
from Backend.backtester import backtest_strategy  # Ensure this function is correctly implemented

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestScreen(Screen):
    api_manager = ObjectProperty(None)
    selected_strategy = StringProperty('')
    strategy_params = DictProperty({})

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


        # Output Boxes Layout
        self.outputs_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)

        # Create four equally sized boxes with styled backgrounds
        self.sharpe_box = self.create_output_box('Sharpe Ratio', 'N/A')
        self.initial_box = self.create_output_box('Initial Portfolio', 'N/A')
        self.final_box = self.create_output_box('Final Portfolio', 'N/A')
        self.trades_box = self.create_output_box('Number of Trades', 'N/A')

        # Add boxes to outputs_layout
        self.outputs_layout.add_widget(self.sharpe_box)
        self.outputs_layout.add_widget(self.initial_box)
        self.outputs_layout.add_widget(self.final_box)
        self.outputs_layout.add_widget(self.trades_box)

        # Add outputs_layout to main_layout
        self.main_layout.add_widget(self.outputs_layout)

        # Run Backtest Button
        self.run_backtest_button = Button(
            text="Run Backtest",
            size_hint=(1, 0.05),
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),  # Green
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        self.run_backtest_button.bind(on_release=self.run_backtest)
        self.main_layout.add_widget(self.run_backtest_button)

        # Graph Plot Layout
        self.plot_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6), spacing=10, padding=(0, 10))

        # Add a placeholder label
        self.plot_placeholder = Label(
            text="No backtest run yet.",
            font_size='18sp',
            color=get_color_from_hex('#7f8c8d')
        )
        self.plot_layout.add_widget(self.plot_placeholder)

        # Add plot_layout to main_layout
        self.main_layout.add_widget(self.plot_layout)

        # Navigation Buttons Layout
        self.navigation_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=10)

        strategies_button = Button(
            text="Strategies",
            size_hint=(0.4, 1),  # Adjusted size_hint_x
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),  # Blue
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        strategies_button.bind(on_release=self.go_to_strategies)

        dashboard_button = Button(
            text="Dashboard",
            size_hint=(0.4, 1),  # Adjusted size_hint_x
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),  # Green
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='18sp'
        )
        dashboard_button.bind(on_release=self.go_to_dashboard)

        # Wrap buttons in containers with fixed width
        strategies_container = BoxLayout(size_hint=(None, 1), width=200)  # Adjust width as needed
        strategies_container.add_widget(strategies_button)

        dashboard_container = BoxLayout(size_hint=(None, 1), width=200)  # Adjust width as needed
        dashboard_container.add_widget(dashboard_button)

        self.navigation_buttons_layout.add_widget(strategies_container)
        self.navigation_buttons_layout.add_widget(dashboard_container)

        # Add navigation_buttons_layout to main_layout
        self.main_layout.add_widget(self.navigation_buttons_layout)

        # Add main layout to the screen
        self.add_widget(self.main_layout)

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

    def update_main_rect(self, instance, value):
        """Updates the main_layout background rectangle."""
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def go_to_strategies(self, instance):
        self.manager.current = 'strategies'

    def go_to_dashboard(self, instance):
        self.manager.current = 'dashboard'

    def set_strategy(self, strategy_name, params):
        """
        Sets the selected strategy and its parameters.
        """
        self.selected_strategy = strategy_name
        self.strategy_params = params
        # You can add additional logic here if needed

    def run_backtest(self, instance):
        """
        Executes the backtesting process.
        """
        # Example backtesting logic
        logger.info(f"Running backtest for strategy: {self.selected_strategy} with params: {self.strategy_params}")

        # Extract general parameters
        symbol = self.strategy_params.get('symbol')
        start_date = self.strategy_params.get('start_date')
        end_date = self.strategy_params.get('end_date')
        interval = self.strategy_params.get('interval')

        # Strategy-specific parameters
        strategy_specific_params = {k: v for k, v in self.strategy_params.items() if
                                    k not in ['symbol', 'start_date', 'end_date', 'interval']}

        # Map strategy names to classes
        strategy_map = {
            'Moving Average Crossover': MovingAverageCrossoverStrategy,
            'RSI Strategy': RsiStrategy,
            'Bollinger Bands Strategy': BollingerBandsStrategy
        }

        strategy_class = strategy_map.get(self.selected_strategy)

        if not strategy_class:
            self.display_error_message("Selected strategy is not supported.")
            return

        try:
            # Execute the backtest
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

        # Update the matplotlib figure
        # Remove placeholder if exists
        if self.plot_placeholder in self.plot_layout.children:
            self.plot_layout.remove_widget(self.plot_placeholder)

        # Clear any existing plot
        self.plot_layout.clear_widgets()

        # Add the new figure
        self.graph_plot = FigureCanvasKivyAgg(fig)
        self.plot_layout.add_widget(self.graph_plot)
        plt.close(fig)

        # Update output boxes
        self.sharpe_box.children[0].text = f"{sharpe_ratio:.2f}"
        self.initial_box.children[0].text = f"${initial_portfolio:.2f}"
        self.final_box.children[0].text = f"${final_portfolio:.2f}"
        self.trades_box.children[0].text = f"{num_trades}"
    def on_leave(self):
        """Called when the screen is left."""
        # Clear the plot layout
        self.plot_layout.clear_widgets()


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


