import matplotlib
matplotlib.use('Agg')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from ui.dashboard_screen import DashboardScreen
from ui.active_positions_screen import ActivePositionsScreen
from ui.strategies_screen import StrategiesScreen
from ui.backtesting_screen import BacktestScreen
from ui.stock_data_screen import StockDataScreen
from ui.Live_Trading_Screen import LiveTradingScreen, OrdersScreen
import ui
from Backend.api_manager import APIManager
from kivy.config import Config
Config.set('graphics', 'width', '1600')  # Increased width
Config.set('graphics', 'height', '900')  # Increased height



class MyScreenManager(ScreenManager):
    pass

class PortfolioApp(App):
    def build(self):
        self.api_manager = APIManager()

        sm = MyScreenManager()
        sm.add_widget(DashboardScreen(name='dashboard', api_manager=self.api_manager))
        sm.add_widget(ActivePositionsScreen(name='active_positions', api_manager=self.api_manager))
        sm.add_widget(StrategiesScreen(name='strategies', api_manager=self.api_manager))
        sm.add_widget(BacktestScreen(name='backtest', api_manager=self.api_manager))
        sm.add_widget(StockDataScreen(name='stock_data', api_manager=self.api_manager))
        sm.add_widget(LiveTradingScreen(name='live_trading'))
        sm.add_widget(OrdersScreen(name='orders'))

        sm.current = 'dashboard'

        return sm

if __name__ == '__main__':
    PortfolioApp().run()