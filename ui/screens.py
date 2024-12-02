from kivy.uix.screenmanager import Screen
from Backend.trading_algorithms import Strategy
from Backend.api_manager import APIManager
from kivy.clock import Clock

class DashboardScreen(Screen):
    def on_enter(self):
        Clock.schedule_interval(self.update_data, 60)  # Update every 60 seconds

    def update_data(self, dt):
        data = self.manager.backend.get_portfolio_data()
        # Update UI elements with new data


class AlgorithmScreen(Screen):

    def start_algorithm(self):
        # Get parameters from UI
        parameters = {}
        pass
class PositionsScreen(Screen):

    def on_enter(self):
        Clock.schedule_interval(self.update_positions, 60)  # Update every 60 seconds

    def update_positions(self, dt):
        positions = self.manager
        # Update UI elements with new positions