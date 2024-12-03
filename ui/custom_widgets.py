# ui/custom_widgets.
# ui/custom_widgets.py

# ui/custom_widgets.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex
from utils import hex_to_rgb  # Importing the standalone function

class PositionItem(BoxLayout):
    def __init__(self, position, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.size_hint_y = None
        self.height = 50

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
        price_change_layout = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=150, spacing=5)
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

    def __init__(self, strategy, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.size_hint_y = None
        self.height = 60

        # Set background with rounded corners
        with self.canvas.before:
            Color(*hex_to_rgb('#ffffff'))  # White background
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Strategy Name
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

        # Description
        desc_label = Label(
            text=strategy.get('description', 'No description provided.'),
            font_size='16sp',
            color=get_color_from_hex('#7f8c8d'),
            halign='left',
            valign='middle'
        )
        desc_label.bind(size=desc_label.setter('text_size'))
        desc_label.size_hint_x = 0.6

        self.add_widget(name_label)
        self.add_widget(desc_label)

    def update_bg(self, instance, value):
        """Updates the background's position and size."""
        self.bg.pos = instance.pos
        self.bg.size = instance.size
