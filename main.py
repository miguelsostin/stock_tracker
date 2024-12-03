import matplotlib
matplotlib.use('Agg')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from ui.dashboard_screen import DashboardScreen
from ui.active_positions_screen import ActivePositionsScreen
from ui.strategies_screen import StrategiesScreen
from ui.backtesting_screen import BacktestScreen
from Backend.api_manager import APIManager


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

        sm.current = 'dashboard'

        return sm

if __name__ == '__main__':
    PortfolioApp().run()