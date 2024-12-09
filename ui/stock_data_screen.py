# ui/stock_data_screen.py

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from functools import partial
import pytz
import webbrowser
import tempfile
import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.text import LabelBase

class StockDataScreen(Screen):
    # Properties for displaying price and change information
    current_price = NumericProperty(0.0)
    price_change = NumericProperty(0.0)
    percent_change = NumericProperty(0.0)

    # Reference to API Manager or any backend service if needed
    api_manager = ObjectProperty(None)

    def __init__(self, api_manager, **kwargs):
        super().__init__(**kwargs)
        self.api_manager = api_manager
        self.indicators = {
            'SMA': [],
            'RSI': [],
            'Bollinger Bands': []
        }
        self.temp_files = []
        self.build_ui()

    def build_ui(self):
        # Main Layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Set Background Color for main_layout
        with main_layout.canvas.before:
            Color(*self.hex_to_rgb('#f0f4f7'))  # Light grayish-blue background
            self.main_rect = Rectangle(pos=self.pos, size=self.size)
        main_layout.bind(pos=self.update_main_rect, size=self.update_main_rect)

        # Header with Ticker Input
        header = BoxLayout(size_hint=(1, 0.15), padding=(0, 10), spacing=10)

        # Header Label
        header_label = Label(
            text="📊 Stock Data Visualization",
            font_size='32sp',
            bold=True,
            color=get_color_from_hex('#34495e'),
            halign="left",
            valign="middle"
        )
        header_label.bind(size=header_label.setter('text_size'))

        # Ticker Search Bar Layout
        ticker_input_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(0.4, 1))
        ticker_label = Label(
            text="Ticker:",
            font_size='18sp',
            color=get_color_from_hex('#34495e'),
            size_hint=(0.3, 1),
            halign="right",
            valign="middle"
        )
        ticker_label.bind(size=ticker_label.setter('text_size'))

        self.ticker_input = TextInput(
            text='AAPL',  # Default ticker
            multiline=False,
            size_hint=(0.7, 1),
            hint_text='Enter Ticker'
        )

        search_button = Button(
            text="Search",
            size_hint=(0.4, 1),
            background_color=get_color_from_hex('#2980b9'),
            color=get_color_from_hex('#ffffff'),
            bold=True
        )
        search_button.bind(on_release=self.on_ticker_search)

        ticker_input_layout.add_widget(ticker_label)
        ticker_input_layout.add_widget(self.ticker_input)
        ticker_input_layout.add_widget(search_button)

        header.add_widget(header_label)
        header.add_widget(ticker_input_layout)
        main_layout.add_widget(header)

        # Data Range and Candle Interval Selection Grid
        selection_grid = GridLayout(cols=2, size_hint=(1, 0.15), spacing=20)

        # Data Range Selector
        data_range_layout = self.create_selection_layout(
            title="Data Range (Days):",
            spinner_id="data_range_spinner",
            values=[],
            default_text="Select Range",
            on_text=self.on_data_range_change
        )
        selection_grid.add_widget(data_range_layout)

        # Candle Interval Selector
        candle_interval_layout = self.create_selection_layout(
            title="Candle Interval:",
            spinner_id="candle_interval_spinner",
            values=[],
            default_text="Select Interval",
            on_text=self.on_candle_interval_change
        )
        selection_grid.add_widget(candle_interval_layout)

        main_layout.add_widget(selection_grid)

        # Indicators Selection Grid
        indicators_selection = GridLayout(cols=3, size_hint=(1, 0.2), spacing=20)

        # SMA Selector
        sma_layout = self.create_selection_layout(
            title="Add SMA:",
            spinner_id="sma_spinner",
            values=[],
            default_text="Select SMA",
            on_text=self.on_sma_select
        )
        indicators_selection.add_widget(sma_layout)

        # RSI Selector
        rsi_layout = self.create_selection_layout(
            title="Add RSI:",
            spinner_id="rsi_spinner",
            values=[],
            default_text="Select RSI",
            on_text=self.on_rsi_select
        )
        indicators_selection.add_widget(rsi_layout)

        # Bollinger Bands Selector
        bb_layout = self.create_bb_selection_layout()
        indicators_selection.add_widget(bb_layout)

        main_layout.add_widget(indicators_selection)

        # Selected Indicators Display
        indicators_display = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=10, padding=10)
        indicators_display.add_widget(
            Label(text="Selected Indicators:", size_hint=(0.3, 1), color=get_color_from_hex('#34495e')))
        self.indicators_labels = BoxLayout(orientation='horizontal', size_hint=(0.7, 1), spacing=5)
        indicators_display.add_widget(self.indicators_labels)
        main_layout.add_widget(indicators_display)

        # Plot/Refresh Button
        plot_button = self.create_nav_button(
            text="Plot/Refresh",
            background_color='#2980b9',
            on_release=self.update_plot
        )
        main_layout.add_widget(plot_button)

        dashboard_button = Button(
            text="Back to Dashboard",
            background_color='#34495e',
            on_release=self.go_to_dash
        )
        layout_b = BoxLayout(orientation='vertical', size_hint=(1, 0.1))
        layout_b.add_widget(dashboard_button)

        main_layout.add_widget(layout_b)



        # Spacer
        spacer = BoxLayout(size_hint=(1, 0.05))
        main_layout.add_widget(spacer)

        # Footer (Optional)
        footer = BoxLayout(size_hint=(1, 0.05))
        with footer.canvas.before:
            Color(*self.hex_to_rgb('#f0f4f7'))
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

        # Initialize Selectors
        self.initialize_selectors()
    def go_to_dash(self, instance):
        self.manager.current = 'dashboard'

    def create_selection_layout(self, title, spinner_id, values, default_text, on_text):
        layout = BoxLayout(orientation='vertical', spacing=5)
        label = Label(text=title, size_hint=(1, 0.3), color=get_color_from_hex('#34495e'))
        spinner = Spinner(
            text=default_text,
            values=values,
            size_hint=(1, 0.7)
        )
        spinner.bind(text=on_text)
        setattr(self, spinner_id, spinner)
        layout.add_widget(label)
        layout.add_widget(spinner)
        return layout

    def create_bb_selection_layout(self):
        layout = BoxLayout(orientation='vertical', spacing=5)
        label = Label(text="Add BB:", size_hint=(1, 0.3), color=get_color_from_hex('#34495e'))
        params_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.7))
        self.bb_period_spinner = Spinner(
            text='Period',
            values=[],
            size_hint=(0.6, 1)
        )
        self.bb_std_spinner = Spinner(
            text='Std Dev',
            values=('1', '1.5', '2', '2.5', '3'),
            size_hint=(0.4, 1)
        )
        params_layout.add_widget(self.bb_period_spinner)
        params_layout.add_widget(self.bb_std_spinner)
        self.bb_add_button = Button(
            text="Add BB",
            size_hint=(1, 1),
            background_color=get_color_from_hex('#27ae60'),
            color=get_color_from_hex('#ffffff'),
            bold=True
        )
        self.bb_add_button.bind(on_release=self.on_bb_add)
        layout.add_widget(label)
        layout.add_widget(params_layout)
        layout.add_widget(self.bb_add_button)
        return layout

    def create_nav_button(self, text, background_color, on_release):
        button = Button(
            text=text,
            background_color=get_color_from_hex(background_color),
            font_size='18sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            background_normal=''
        )
        button.bind(on_release=on_release)

        with button.canvas.before:
            Color(*self.hex_to_rgb(background_color))
            nav_bg = RoundedRectangle(pos=button.pos, size=button.size, radius=[20])
        button.bind(pos=lambda instance, value: self.update_nav_bg(instance, nav_bg),
                    size=lambda instance, value: self.update_nav_bg(instance, nav_bg))

        return button

    def update_main_rect(self, instance, value):
        self.main_rect.pos = instance.pos
        self.main_rect.size = instance.size

    def update_footer_rect(self, instance, value):
        self.footer_rect.pos = instance.pos
        self.footer_rect.size = instance.size

    def update_nav_bg(self, instance, nav_bg):
        nav_bg.pos = instance.pos
        nav_bg.size = instance.size

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def initialize_selectors(self):
        self.candle_interval_spinner.values = ('1m', '2m', '5m', '15m', '30m', '60m', '1h', '1d')
        self.candle_interval_spinner.text = '1d'
        self.on_candle_interval_change(self.candle_interval_spinner, '1d')

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def on_ticker_search(self, instance):
        """Handles ticker input search."""
        ticker = self.ticker_input.text.strip().upper()
        if not ticker:
            self.show_error("Please enter a valid ticker symbol.")
            return
        print(f"Selected Ticker: {ticker}")

    def on_data_range_change(self, spinner, text):
        try:
            data_range = int(text)
        except ValueError:
            data_range = 30

        interval = self.candle_interval_spinner.text
        minute_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '1h']

        if interval in minute_intervals:
            try:
                interval_minutes = int(interval[:-1])
                candles_per_hour = 60 // interval_minutes
            except ValueError:
                candles_per_hour = 60
            candles_per_day = 24 * candles_per_hour
            num_candles = 7 * candles_per_day
        else:
            num_candles = data_range

        max_sma = num_candles // 3
        if max_sma < 2:
            max_sma = 2

        sma_options = []
        period = 2
        while period <= max_sma:
            sma_options.append(str(period))
            period *= 2
        if not sma_options:
            sma_options = [str(max_sma)]

        self.sma_spinner.values = sma_options
        self.sma_spinner.text = 'Select SMA'

        max_rsi = num_candles // 10
        if max_rsi < 5:
            max_rsi = 5

        rsi_options = [str(i) for i in range(5, max_rsi + 1, 5)]
        if not rsi_options:
            rsi_options = ['14']

        self.rsi_spinner.values = rsi_options
        self.rsi_spinner.text = 'Select RSI'

        max_bb_period = num_candles // 5
        if max_bb_period < 10:
            max_bb_period = 10

        bb_period_options = [str(i) for i in range(10, max_bb_period + 1, 5)]
        if not bb_period_options:
            bb_period_options = ['20']

        self.bb_period_spinner.values = bb_period_options
        self.bb_period_spinner.text = 'Period'

        self.bb_std_spinner.text = 'Std Dev'

    def on_candle_interval_change(self, spinner, text):
        minute_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '1h']
        daily_intervals = ['1d', '1wk', '1mo']

        if text in minute_intervals:
            self.data_range_spinner.values = tuple(str(i) for i in range(1, 8))
            current_range = self.data_range_spinner.text
            if current_range not in self.data_range_spinner.values:
                self.data_range_spinner.text = '7'
                self.on_data_range_change(self.data_range_spinner, '7')
        elif text in daily_intervals:
            self.data_range_spinner.values = ('7', '14', '30', '60', '90', '180', '365')
            current_range = self.data_range_spinner.text
            if current_range not in self.data_range_spinner.values:
                self.data_range_spinner.text = '30'
                self.on_data_range_change(self.data_range_spinner, '30')
        else:
            self.data_range_spinner.values = ('7', '14', '30', '60', '90', '180', '365')
            current_range = self.data_range_spinner.text
            if current_range not in self.data_range_spinner.values:
                self.data_range_spinner.text = '30'
                self.on_data_range_change(self.data_range_spinner, '30')

        self.on_data_range_change(self.data_range_spinner, self.data_range_spinner.text)

    def on_sma_select(self, spinner, text):
        if text == 'Select SMA' or f"SMA{text}" in self.indicators['SMA']:
            return
        self.indicators['SMA'].append(f"SMA{text}")
        self.update_indicators_display()
        spinner.text = 'Select SMA'

    def on_rsi_select(self, spinner, text):
        if text == 'Select RSI' or f"RSI{text}" in self.indicators['RSI']:
            return
        self.indicators['RSI'].append(f"RSI{text}")
        self.update_indicators_display()
        spinner.text = 'Select RSI'

    def on_bb_add(self, instance):
        period = self.bb_period_spinner.text
        std_dev = self.bb_std_spinner.text

        if period == 'Period' or std_dev == 'Std Dev':
            self.show_error("Please select both Period and Std Dev for Bollinger Bands.")
            return

        bb_config = f"BB({period},{std_dev})"
        if bb_config in self.indicators['Bollinger Bands']:
            self.show_error("This Bollinger Bands configuration is already added.")
            return

        self.indicators['Bollinger Bands'].append(bb_config)
        self.update_indicators_display()

        self.bb_period_spinner.text = 'Period'
        self.bb_std_spinner.text = 'Std Dev'

    def update_indicators_display(self):
        self.indicators_labels.clear_widgets()
        for category, configs in self.indicators.items():
            for config in configs:
                box = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=150, spacing=5)
                lbl = Label(text=config, size_hint=(0.7, 1), color=get_color_from_hex('#34495e'))
                btn = Button(
                    text='X',
                    size_hint=(0.3, 1),
                    background_color=get_color_from_hex('#e74c3c'),
                    color=get_color_from_hex('#ffffff'),
                    bold=True
                )
                btn.bind(on_release=partial(self.remove_indicator, config))
                box.add_widget(lbl)
                box.add_widget(btn)
                self.indicators_labels.add_widget(box)

    def remove_indicator(self, config, instance):
        category = self.get_indicator_category(config)
        if category and config in self.indicators.get(category, []):
            self.indicators[category].remove(config)
            self.update_indicators_display()

    def get_indicator_category(self, config):
        if config.startswith('SMA'):
            return 'SMA'
        elif config.startswith('RSI'):
            return 'RSI'
        elif config.startswith('BB'):
            return 'Bollinger Bands'
        return None

    def update_plot(self, *args):
        ticker = self.ticker_input.text.strip().upper()
        data_range_text = self.data_range_spinner.text
        interval = self.candle_interval_spinner.text

        if not ticker:
            self.show_error("Please enter a valid ticker symbol before plotting.")
            return

        try:
            data_range = int(data_range_text)
        except ValueError:
            self.show_error("Invalid data range selected.")
            return

        minute_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '1h']
        if interval in minute_intervals:
            max_supported_days = 7
            if data_range > max_supported_days:
                data_range = max_supported_days
                self.data_range_spinner.text = '7'
                self.on_data_range_change(self.data_range_spinner, '7')

        total_days = data_range
        data = self.fetch_data(ticker, total_days, interval)
        if data is None or data.empty:
            self.current_price = 0.0
            self.price_change = 0.0
            self.percent_change = 0.0
            return

        if interval in minute_intervals:
            data_to_plot = data.copy()
        else:
            try:
                end_date = data.index.max()
                start_date = end_date - timedelta(days=data_range)
                data_to_plot = data[data.index >= start_date]
            except Exception as e:
                self.show_error(f"Error slicing data: {e}")
                return

        try:
            latest_close = data_to_plot['Close'].iloc[-1]
            prev_close = data_to_plot['Close'].iloc[-2] if len(data_to_plot) > 1 else latest_close
            change = latest_close - prev_close
            pct_change = (change / prev_close) * 100 if prev_close != 0 else 0
        except IndexError:
            latest_close = 0
            change = 0
            pct_change = 0

        self.current_price = float(latest_close)
        self.price_change = float(change)
        self.percent_change = float(pct_change)

        data_for_plot = data_to_plot.copy()
        data_for_plot.index = pd.to_datetime(data_for_plot.index)
        non_trading_end_times = self.detect_non_trading_periods(data_for_plot, interval)

        has_rsi = len(self.indicators['RSI']) > 0
        rows = 2 if has_rsi else 1
        subplot_titles = [f"{ticker} Stock Price"]
        if has_rsi:
            subplot_titles.append("Relative Strength Index (RSI)")

        specs = []
        if rows == 2:
            specs = [
                [{"secondary_y": True}],
                [{}]
            ]
        else:
            specs = [
                [{"secondary_y": True}]
            ]

        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=subplot_titles,
            row_heights=[0.7, 0.3] if has_rsi else [1.0],
            specs=specs
        )

        fig.add_trace(go.Candlestick(
            x=data_for_plot.index,
            open=data_for_plot['Open'],
            high=data_for_plot['High'],
            low=data_for_plot['Low'],
            close=data_for_plot['Close'],
            name='Candlesticks'
        ), row=1, col=1, secondary_y=False)

        fig.add_trace(go.Bar(
            x=data_for_plot.index,
            y=data_for_plot['Volume'],
            marker_color='rgba(0, 0, 255, 0.3)',
            name='Volume',
            yaxis='y2'
        ), row=1, col=1, secondary_y=True)

        sma_colors = ['orange', 'purple', 'cyan', 'magenta', 'brown', 'pink']
        for idx, sma in enumerate(self.indicators['SMA']):
            sma_period = int(sma.replace('SMA', ''))
            sma_series = data_for_plot['Close'].rolling(window=sma_period).mean()
            fig.add_trace(go.Scatter(
                x=data_for_plot.index,
                y=sma_series,
                mode='lines',
                line=dict(color=sma_colors[idx % len(sma_colors)], width=1),
                name=f'SMA{sma_period}'
            ), row=1, col=1, secondary_y=False)

        for bb in self.indicators['Bollinger Bands']:
            parts = bb.strip('BB()').split(',')
            if len(parts) != 2:
                continue
            bb_period, bb_std_dev = int(parts[0]), float(parts[1])
            bb_mid = data_for_plot['Close'].rolling(window=bb_period).mean()
            bb_std = data_for_plot['Close'].rolling(window=bb_period).std()
            bb_up = bb_mid + (bb_std_dev * bb_std)
            bb_down = bb_mid - (bb_std_dev * bb_std)

            fig.add_trace(go.Scatter(
                x=data_for_plot.index,
                y=bb_up,
                mode='lines',
                line=dict(color='gray', dash='dash'),
                name=f'BB Upper ({bb_period},{bb_std_dev})'
            ), row=1, col=1, secondary_y=False)

            fig.add_trace(go.Scatter(
                x=data_for_plot.index,
                y=bb_down,
                mode='lines',
                line=dict(color='gray', dash='dash'),
                name=f'BB Lower ({bb_period},{bb_std_dev})',
                fill='tonexty',
                fillcolor='rgba(128, 128, 128, 0.1)'
            ), row=1, col=1, secondary_y=False)

        if has_rsi:
            rsi_colors = ['purple', 'green', 'red', 'blue']
            for idx, rsi in enumerate(self.indicators['RSI']):
                rsi_period = int(rsi.replace('RSI', ''))
                rsi_series = self.calculate_rsi(data_for_plot['Close'], rsi_period)
                fig.add_trace(go.Scatter(
                    x=data_for_plot.index,
                    y=rsi_series,
                    mode='lines',
                    line=dict(color=rsi_colors[idx % len(rsi_colors)], width=1),
                    name=f'RSI{rsi_period}'
                ), row=2, col=1)
            fig.update_yaxes(range=[0, 100], row=2, col=1)

        fixed_width = pd.Timedelta(minutes=10)
        for end_time in non_trading_end_times:
            fig.add_vrect(
                x0=end_time,
                x1=end_time + fixed_width,
                fillcolor="LightSalmon",
                opacity=0.2,
                line_width=0,
                layer="below",
                row=1,
                col=1
            )

        fig.update_layout(
            title=f"{ticker} Stock Price",
            legend=dict(x=0, y=1.2, orientation='h'),
            margin=dict(l=40, r=40, t=80, b=40),
            height=900,
            xaxis_rangeslider_visible=False
        )

        volume_max = data_for_plot['Volume'].max()
        fig.update_yaxes(
            title_text="Volume",
            row=1,
            col=1,
            secondary_y=True,
            range=[0, volume_max * 1.5]
        )
        fig.update_yaxes(
            title_text="Price",
            row=1,
            col=1,
            secondary_y=False
        )

        plot_html = fig.to_html(include_plotlyjs='cdn')
        tmp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(tmp_dir, 'current_plot.html')

        with open(tmp_file_path, 'w', encoding='utf-8') as tmp_file:
            tmp_file.write(plot_html)

        if tmp_file_path not in self.temp_files:
            self.temp_files.append(tmp_file_path)

        unique_query = f"?{datetime.now().timestamp()}"
        webbrowser.open_new_tab(f'file://{os.path.abspath(tmp_file_path)}{unique_query}')

        self.show_notification("Plot Generated", "The Plotly chart has been opened in your default web browser.")

    def fetch_data(self, ticker, total_days, interval):
        end = datetime.now(pytz.UTC)
        if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '1h']:
            start = end - timedelta(days=7)
        else:
            start = end - timedelta(days=total_days)

        try:
            data = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
        except Exception as e:
            self.show_error(f"Error fetching data: {e}")
            return None

        if data.empty:
            print(f"No data found for {ticker}.")
            self.show_error(f"No data found for ticker '{ticker}'. Please check the ticker symbol and try again.")
            return None

        if data.index.tz is None:
            data = data.tz_localize(pytz.UTC).tz_convert('US/Eastern')
        else:
            data = data.tz_convert('US/Eastern')

        data.columns = data.columns.get_level_values(0)
        print(f"Fetched {len(data)} rows of data for {ticker} with interval {interval}.")
        return data

    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def detect_non_trading_periods(self, data, interval):
        if interval.endswith('m') or interval.endswith('h'):
            trading_end_hour = 16
            trading_end_minute = 0
        else:
            return []

        non_trading_end_times = []
        sorted_index = sorted(data.index)
        previous_time = None
        for current_time in sorted_index:
            if previous_time is not None:
                gap = current_time - previous_time
                if interval.endswith('m'):
                    expected_gap = pd.Timedelta(minutes=int(interval[:-1]))
                elif interval.endswith('h'):
                    expected_gap = pd.Timedelta(hours=int(interval[:-1]))
                else:
                    expected_gap = pd.Timedelta(days=1)

                if gap > expected_gap:
                    trading_close = previous_time.replace(hour=trading_end_hour, minute=trading_end_minute, second=0,
                                                          microsecond=0)
                    non_trading_end_times.append(trading_close)
            previous_time = current_time
        return non_trading_end_times

    def show_error(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message, halign="center", valign="middle"),
            size_hint=(0.6, 0.4)
        )
        popup.open()

    def show_notification(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, halign="center", valign="middle"),
            size_hint=(0.6, 0.4)
        )
        popup.open()

    def on_stop(self):
        for file_path in self.temp_files:
            try:
                os.remove(file_path)
                print(f"Deleted temporary file: {file_path}")
            except Exception as e:
                print(f"Error deleting temporary file {file_path}: {e}")