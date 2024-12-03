# ui/active_positions_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from ui.custom_widgets import PositionItem  # Ensure this widget is styled consistently
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.scrollview import ScrollView
from utils import hex_to_rgb  # Importing the standalone function
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActivePositionsScreen(Screen):
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
            Color(*hex_to_rgb('#f0f4f7'))  # Light grayish-blue background
            self.main_rect = Rectangle(pos=self.pos, size=self.size)
        main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Header
        header = BoxLayout(size_hint=(1, 0.1), padding=(0, 10), spacing=10)
        header_label = Label(
            text="📊 Active Positions",
            font_size='28sp',
            bold=True,
            color=get_color_from_hex('#34495e')
            # font_name="Roboto"  # Uncomment if using custom font
        )
        header.add_widget(header_label)
        main_layout.add_widget(header)

        # Table Headers
        table_headers = self.create_table_headers()
        main_layout.add_widget(table_headers)

        # Positions Container
        positions_container = GridLayout(cols=1, spacing=10, size_hint=(1, 0.75))
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        self.scroll_layout = scroll_layout  # Store reference for updates

        try:
            positions = self.api_manager.get_all_positions()
            if positions:
                for position in positions:
                    item = PositionItem(position=position)
                    scroll_layout.add_widget(item)
            else:
                no_positions_label = Label(
                    text="No active positions.",
                    font_size='18sp',
                    color=get_color_from_hex('#7f8c8d'),
                    size_hint_y=None,
                    height=40
                )
                scroll_layout.add_widget(no_positions_label)
        except Exception as e:
            error_label = Label(
                text="Error fetching positions.",
                font_size='18sp',
                color=get_color_from_hex('#e74c3c'),
                size_hint_y=None,
                height=40
            )
            scroll_layout.add_widget(error_label)
            logger.error(f"Error fetching positions: {e}")

        scroll_view.add_widget(scroll_layout)
        positions_container.add_widget(scroll_view)
        main_layout.add_widget(positions_container)

        # Spacer
        spacer = BoxLayout(size_hint=(1, 0.05))
        main_layout.add_widget(spacer)

        # Back Button
        back_button = self.create_back_button(
            text="Back to Dashboard",
            background_color='#2980b9',
            on_release=self.go_to_dashboard
        )
        main_layout.add_widget(back_button)

        # Footer
        footer = BoxLayout(size_hint=(1, 0.05))
        with footer.canvas.before:
            Color(*hex_to_rgb('#f0f4f7'))  # Match main_layout background
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

    def create_table_headers(self):
        """Creates a header row for the positions table."""
        headers = ["Symbol", "Current Price", "Quantity", "Market Value", "P&L"]
        header_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30, spacing=10)

        for header in headers:
            label = Label(
                text=header,
                font_size='18sp',
                bold=True,
                color=get_color_from_hex('#34495e'),
                halign='center',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))  # Ensures text is centered
            header_layout.add_widget(label)

        # Add a bottom border to the header
        with header_layout.canvas.after:
            Color(*hex_to_rgb('#bdc3c7'))  # Light gray border
            self.header_border = Rectangle(pos=(header_layout.x, header_layout.y - 2),
                                           size=(header_layout.width, 2))
        header_layout.bind(pos=self.update_header_border, size=self.update_header_border)

        return header_layout

    def update_header_border(self, instance, value):
        """Updates the header border position and size."""
        self.header_border.pos = (instance.x, instance.y - 2)
        self.header_border.size = (instance.width, 2)

    def create_back_button(self, text, background_color, on_release):
        """Helper method to create a styled back button."""
        button = Button(
            text=text,
            background_normal='',  # Allows background_color to take effect
            background_color=background_color,
            font_size='18sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            size_hint=(1, 0.1)
        )
        button.bind(on_release=on_release)

        # Add rounded corners
        with button.canvas.before:
            Color(*hex_to_rgb(background_color))
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

    def update_header_border(self, instance, value):
        """Updates the header border position and size."""
        self.header_border.pos = (instance.x, instance.y - 2)
        self.header_border.size = (instance.width, 2)

    def update_nav_bg(self, instance, nav_bg):
        """Updates the navigation button background."""
        nav_bg.pos = instance.pos
        nav_bg.size = instance.size

    def on_enter(self):
        """Called when the screen is entered."""
        self.update_positions()
        # Schedule periodic updates every 60 seconds
        self.update_event = Clock.schedule_interval(self.update_positions, 60)

    def on_leave(self):
        """Called when the screen is left."""
        self.update_event.cancel()

    def update_positions(self, *args):
        """Fetches and updates all active positions."""
        logger.info("Updating active positions...")
        try:
            positions = self.api_manager.get_all_positions()
            self.scroll_layout.clear_widgets()
            if positions:
                for position in positions:
                    item = PositionItem(position=position)
                    self.scroll_layout.add_widget(item)
            else:
                no_positions_label = Label(
                    text="No active positions.",
                    font_size='18sp',
                    color=get_color_from_hex('#7f8c8d'),
                    size_hint_y=None,
                    height=40
                )
                self.scroll_layout.add_widget(no_positions_label)
        except Exception as e:
            self.scroll_layout.clear_widgets()
            error_label = Label(
                text="Error fetching positions.",
                font_size='18sp',
                color=get_color_from_hex('#e74c3c'),
                size_hint_y=None,
                height=40
            )
            self.scroll_layout.add_widget(error_label)
            logger.error(f"Error updating positions: {e}")

    def go_to_dashboard(self, instance):
        """Navigate back to the Dashboard screen."""
        self.manager.current = 'dashboard'
