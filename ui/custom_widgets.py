# ui/custom_widgets.
# ui/custom_widgets.py

# ui/custom_widgets.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex
from utils import hex_to_rgb  # Importing the standalone function
from kivy.properties import NumericProperty, ObjectProperty
import json
import yfinance as yf

class PositionItem(BoxLayout):
    def __init__(self, position, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.size_hint_y = None
        self.height = 80

        # Set background with rounded corners
        with self.canvas.before:
            Color(*hex_to_rgb('#ffffff'))  # White background
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Symbol Label
        symbol = Label(
            text=position.symbol,
            font_size='18sp',
            color=get_color_from_hex('#2c3e50'),
            halign="left",
            valign="middle"
        )
        symbol.bind(size=symbol.setter('text_size'))

        # Current Price and Daily % Change
        current_price = float(position.current_price) if position.current_price else 0.0
        change_today = float(position.change_today) if position.change_today else 0.0

        # Determine color based on change_today
        change_color = '#2ecc71' if change_today >= 0 else '#e74c3c'  # Green if up, red if down
        change_sign = '+' if change_today >= 0 else ''

        # Current Price Label
        price_label = Label(
            text=f"${current_price:,.2f}",
            font_size='18sp',
            color=get_color_from_hex('#2c3e50'),
            halign="center",
            valign="middle"
        )
        price_label.bind(size=price_label.setter('text_size'))

        # Daily % Change Label
        change_label = Label(
            text=f"{change_sign}{change_today:.2f}%",
            font_size='18sp',
            color=get_color_from_hex(change_color),
            halign="left",
            valign="middle"
        )
        change_label.bind(size=change_label.setter('text_size'))

        # Combine price and change in a horizontal BoxLayout
        price_change_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1), width=150, spacing=5)
        price_change_layout.add_widget(price_label)
        price_change_layout.add_widget(change_label)

        # Quantity Label
        quantity = Label(
            text=position.qty,
            font_size='18sp',
            color=get_color_from_hex('#2c3e50'),
            halign="center",
            valign="middle"
        )
        quantity.bind(size=quantity.setter('text_size'))

        # Market Value Label
        market_value = float(position.market_value) if position.market_value else 0.0
        market_value_label = Label(
            text=f"${market_value:,.2f}",
            font_size='18sp',
            color=get_color_from_hex('#2c3e50'),
            halign="center",
            valign="middle"
        )
        market_value_label.bind(size=market_value_label.setter('text_size'))

        # Unrealized P/L Label
        unrealized_pl = float(position.unrealized_pl) if position.unrealized_pl else 0.0
        pl_color = '#2ecc71' if unrealized_pl >= 0 else '#e74c3c'  # Green if positive, red if negative
        pl_sign = '+' if unrealized_pl >= 0 else ''

        pl_label = Label(
            text=f"{pl_sign}${unrealized_pl:,.2f}",
            font_size='18sp',
            color=get_color_from_hex(pl_color),
            halign="center",
            valign="middle"
        )
        pl_label.bind(size=pl_label.setter('text_size'))

        # Add all widgets to the PositionItem
        self.add_widget(symbol)
        self.add_widget(price_change_layout)
        self.add_widget(quantity)
        self.add_widget(market_value_label)
        self.add_widget(pl_label)

    def update_bg(self, instance, value):
        """Updates the background's position and size."""
        self.bg.pos = instance.pos
        self.bg.size = instance.size





# ui/custom_widgets.py


from kivy.properties import StringProperty



class StrategyItem(BoxLayout):
    strategy_name = StringProperty('')
    description = StringProperty('')

    def __init__(self, strategy, on_run_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.size_hint_y = None
        self.height = 60

        with self.canvas.before:
            Color(*hex_to_rgb('#ffffff'))
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.on_run_callback = on_run_callback

        parameters_json = strategy['parameters']
        try:
            loaded_params = json.loads(parameters_json)
        except json.JSONDecodeError:
            loaded_params = {}

        interval = loaded_params.get('interval')
        strategy_class_name = loaded_params.get('strategy_class_name')

        if not interval or not strategy_class_name:
            interval = interval if interval else 'N/A'
            strategy_class_name = strategy_class_name if strategy_class_name else 'UnknownStrategy'

        name_label = Label(
            text=strategy['name'],
            font_size='18sp',
            bold=True,
            color=get_color_from_hex('#2c3e50'),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        name_label.size_hint_x = 0.4

        run_button = Button(
            text='Run',
            size_hint=(0.2, 1),
            background_normal='',
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True,
            font_size='16sp'
        )
        run_button.bind(on_release=lambda instance: self.run_strategy(strategy, loaded_params))

        self.add_widget(name_label)
        self.add_widget(run_button)

    def update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

    def run_strategy(self, strategy, loaded_params):
        if self.on_run_callback:
            self.on_run_callback(strategy, loaded_params)

class ETFAnalyticsWidget(BoxLayout):
    """
    A widget representing a single ETF's analytics displayed in a small square.
    """
    etf_name = StringProperty("SPY")
    current_price = NumericProperty(0.0)
    daily_percent_change = NumericProperty(0.0)
    daily_net_change = NumericProperty(0.0)

    def __init__(self, etf_name, **kwargs):
        super().__init__(**kwargs)
        self.etf_name = etf_name
        self.orientation = "vertical"
        self.padding = 10
        self.size_hint = (1, 0.2)

        # Background styling
        with self.canvas.before:
            Color(*get_color_from_hex("#34495e"))  # Dark blue background
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.update_bg_rect, size=self.update_bg_rect)

        # Labels
        self.name_label = Label(
            text=self.etf_name,
            font_size="16sp",
            bold=True,
            color=get_color_from_hex("#ecf0f1"),  # Light text
            size_hint=(1, 0.3),
        )
        self.price_label = Label(
            text=f"${self.current_price:.2f}",
            font_size="20sp",
            bold=True,
            color=get_color_from_hex("#2ecc71"),  # Green text for price
            size_hint=(1, 0.4),
        )
        self.change_label = Label(
            text=f"{self.daily_percent_change:.2f}% ({self.daily_net_change:+.2f})",
            font_size="14sp",
            color=get_color_from_hex("#e74c3c") if self.daily_percent_change < 0 else get_color_from_hex("#2ecc71"),
            size_hint=(1, 0.3),
        )

        # Add labels to the layout
        self.add_widget(self.name_label)
        self.add_widget(self.price_label)
        self.add_widget(self.change_label)

    def update_bg_rect(self, instance, value):
        """Update the background rectangle position and size."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_analytics(self, quote, change, percent_change):
        """Fetch and update the ETF's analytics."""

        try:
            self.current_price = float(quote)
            self.daily_net_change = float(change)
            self.daily_percent_change = float(percent_change)

            # Update the text on labels
            self.price_label.text = f"${self.current_price:.2f}"
            self.change_label.text = f"{self.daily_percent_change:.2f}% ({self.daily_net_change:+.2f})"
            self.change_label.color = get_color_from_hex("#e74c3c") if self.daily_percent_change < 0 else get_color_from_hex("#2ecc71")
        except Exception as e:
            self.price_label.text = "Error"
            self.change_label.text = "Error"
            print(f"Error fetching data for {self.etf_name}: {e}")

