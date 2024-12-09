# ui/dashboard_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from Backend.api_manager import APIManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.text import LabelBase
from ui.custom_widgets import ETFAnalyticsWidget

# Optional: Register a custom font if desired
# LabelBase.register(name="Roboto", fn_regular="Roboto-Regular.ttf")

class DashboardScreen(Screen):
    net_portfolio_balance = NumericProperty(0.0)
    daily_net_change = NumericProperty(0.0)
    daily_percent_change = NumericProperty(0.0)
    api_manager = ObjectProperty(None)

    def __init__(self, api_manager, **kwargs):
        super().__init__(**kwargs)
        self.api_manager = api_manager
        self.build_ui()

    def build_ui(self):
        # Main Layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Set Background Color for main_layout
        with main_layout.canvas.before:
            Color(*self.hex_to_rgb('#f0f4f7'))  # Light grayish-blue background
            self.main_rect = Rectangle(pos=self.pos, size=self.size)
        main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Header
        header = BoxLayout(size_hint=(1, 0.05), padding=(0, 10), spacing=10)
        header_label = Label(
            text="📈 Portfolio Dashboard",  # Remove emoji if undesired
            font_size='32sp',
            bold=True,
            color=get_color_from_hex('#34495e')
            # font_name="Roboto"  # Uncomment if using custom font
        )
        header.add_widget(header_label)
        main_layout.add_widget(header)



        # Metrics Grid
        self.change_label = Label(
            text="Daily Change: $0.00 (0.00%)",
            font_size='20sp',
            color=get_color_from_hex('#2ecc71'),  # Default to green
            halign="center",
            valign="middle"
        )
        self.change_label.bind(size=self.change_label.setter('text_size'))

        metrics_grid = BoxLayout(orientation='vertical', padding=10, spacing=20, size_hint=(1, 0.2))

        # Net Portfolio Balance

        self.balance_label = self.create_metric_label("Portfolio Balance", "$0.00", '#2c3e50')
        metrics_grid.add_widget(self.balance_label)

        #SPY, QQQ
        etf_analytics_layout = GridLayout(cols=5, size_hint=(1, 0.1), spacing=10)
        self.etf_widgets = [
            ETFAnalyticsWidget(etf_name="SPY"),
            ETFAnalyticsWidget(etf_name="QQQ"),
            ETFAnalyticsWidget(etf_name="DIA"),
            ETFAnalyticsWidget(etf_name="IWM"),
            ETFAnalyticsWidget(etf_name="VTI"),
        ]
        for widget in self.etf_widgets:
            etf_analytics_layout.add_widget(widget)

        main_layout.add_widget(etf_analytics_layout)




        # metrics_grid.add_widget(self.change_label)
        main_layout.add_widget(metrics_grid)

        # Navigation Buttons
        buttons_layout = GridLayout(cols=4, size_hint=(1, 0.15), spacing=20)

        active_positions_button = self.create_nav_button(
            text="Active Positions",
            background_color='#2980b9',  # Pass hex string directly
            on_release=self.go_to_active_positions
        )
        strategies_button = self.create_nav_button(
            text="Strategies",
            background_color='#27ae60',  # Pass hex string directly
            on_release=self.go_to_strategies
        )
        Live_Strategies_button = self.create_nav_button(
            text="Live Strategies",
            background_color='#27ae60',  # Pass hex string directly
            on_release=self.go_to_live_strategies
        )

        Search_Stocks_button = self.create_nav_button(
            text="Search Stocks",
            background_color='#2980b9',  # Pass hex string directly
            on_release=self.go_to_search_stocks
        )

        buttons_layout.add_widget(active_positions_button)
        buttons_layout.add_widget(strategies_button)
        buttons_layout.add_widget(Live_Strategies_button)
        buttons_layout.add_widget(Search_Stocks_button)

        main_layout.add_widget(buttons_layout)

        # Footer (Optional)
        footer = BoxLayout(size_hint=(1, 0.05))
        with footer.canvas.before:
            Color(*self.hex_to_rgb('#f0f4f7'))  # Match main_layout background
            self.footer_rect = Rectangle(pos=footer.pos, size=footer.size)
        footer.bind(pos=self.update_footer_rect, size=self.update_footer_rect)

        footer_label = Label(
            text="© 2024 Stock Tracker",
            font_size='14sp',
            color=get_color_from_hex('#95a5a6')
        )
        footer.add_widget(footer_label)
        main_layout.add_widget(footer)

        self.add_widget(main_layout)

    def create_metric_label(self, title, value, bg_color):
        """Helper method to create a metric display with a colored background."""
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5, size_hint=(1, 1))

        with layout.canvas.before:
            Color(*self.hex_to_rgb(bg_color))
            metric_bg = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[10])
        layout.bind(pos=lambda instance, value: self.update_metric_bg(instance, metric_bg),
                   size=lambda instance, value: self.update_metric_bg(instance, metric_bg))

        title_label = Label(
            text=title,
            font_size='18sp',
            color=get_color_from_hex('#ecf0f1'),
            halign="center",
            valign="middle"
            # font_name="Roboto"  # Uncomment if using custom font
        )
        title_label.bind(size=title_label.setter('text_size'))

        value_label = Label(
            text=value,
            font_size='24sp',
            bold=True,
            color=get_color_from_hex('#ecf0f1'),
            halign="center",
            valign="middle"
            # font_name="Roboto"  # Uncomment if using custom font
        )
        value_label.bind(size=value_label.setter('text_size'))

        layout.add_widget(title_label)
        layout.add_widget(value_label)
        layout.add_widget(self.change_label)

        return layout

    def create_nav_button(self, text, background_color, on_release):
        """Helper method to create a styled navigation button."""
        button = Button(
            text=text,
            background_color=background_color,
            font_size='18sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            background_normal=''  # This allows background_color to take effect
        )
        button.bind(on_release=on_release)

        # Add rounded corners
        with button.canvas.before:
            Color(*self.hex_to_rgb(background_color))
            nav_bg = RoundedRectangle(pos=button.pos, size=button.size, radius=[20])
        # Bind the position and size updates to the nav_bg
        button.bind(pos=lambda instance, value: self.update_nav_bg(instance, nav_bg),
                   size=lambda instance, value: self.update_nav_bg(instance, nav_bg))

        return button

    def update_main_rect(self, instance, value):
        """Updates the main_layout background rectangle."""
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def update_footer_rect(self, instance, value):
        """Updates the footer background rectangle."""
        self.footer_rect.pos = instance.pos
        self.footer_rect.size = instance.size

    def update_metric_bg(self, instance, metric_bg):
        """Updates the metric label background."""
        metric_bg.pos = instance.pos
        metric_bg.size = instance.size

    def update_nav_bg(self, instance, nav_bg):
        """Updates the navigation button background."""
        nav_bg.pos = instance.pos
        nav_bg.size = instance.size

    def hex_to_rgb(self, hex_color):
        """Converts hex color to RGB tuple with values between 0 and 1."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

    def on_enter(self):
        """Called when the screen is entered."""
        self.update_values()
        self.update_event = Clock.schedule_interval(self.update_values, 60)  # Update every minute

    def on_leave(self):
        """Called when the screen is left."""
        self.update_event.cancel()

    def update_values(self, *args):
        """Fetches and updates all dashboard metrics."""
        print("Updating dashboard values...")
        try:
            # Fetch portfolio metrics
            self.net_portfolio_balance = self.api_manager.get_net_portfolio_balance()
            change, percent_change = self.api_manager.get_day_portfolio_change()

            # Update metric labels
            self.balance_label.children[1].text = f"${self.net_portfolio_balance:,.2f}"

            # Update daily change label with color
            self.daily_net_change = change
            self.daily_percent_change = percent_change
            self.update_change_label()
            self.update_etf_analytics(None)

        except Exception as e:
            print(f"Error updating dashboard values: {e}")
            self.balance_label.children[0].text = "Error fetching balance."
            self.change_label.text = "Daily Change: Error fetching change."
            self.change_label.color = get_color_from_hex('#e74c3c')  # Red color for errors

    def update_change_label(self):
        """Updates the daily change label text and color based on the change value."""
        if self.daily_net_change >= 0:
            color = get_color_from_hex('#2ecc71')  # Green color
            change_text = f"Daily Change: +${self.daily_net_change:,.2f} ({self.daily_percent_change:.2f}%)"
        else:
            color = get_color_from_hex('#e74c3c')  # Red color
            change_text = f"Daily Change: -${abs(self.daily_net_change):,.2f} ({self.daily_percent_change:.2f}%)"

        self.change_label.text = change_text
        self.change_label.color = color

    def go_to_active_positions(self, instance):
        """Navigate to the Active Positions screen."""
        self.manager.current = 'active_positions'

    def go_to_strategies(self, instance):
        """Navigate to the Strategies screen."""
        self.manager.current = 'strategies'
    def go_to_search_stocks(self, instance):
        """Navigate to the Stock Data screen."""
        self.manager.current = 'stock_data'

    def update_etf_analytics(self, dt):
        """Update all ETF analytics."""

        for widget in self.etf_widgets:
            dat1,dat2,dat3 = self.api_manager.get_quote_and_change(widget.etf_name)
            widget.update_analytics(dat1,dat2,dat3)
    def go_to_live_strategies(self, instance):
        """Navigate to the Live Trading screen."""
        self.manager.current = 'live_trading'

