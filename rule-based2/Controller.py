from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from Mine import Mines
from WorkerAgent import Workers
from CityWrapper import CitiesWrapper
import sys
import math
import numpy as np

class State:
    def __init__(self, game_state, player, opponent):
        self._update_state(game_state, player, opponent)
        
    def _update_state(self, game_state, player, opponent):
        self.num_workers = sum([1 if unit.is_worker() else 0 for unit in player.units])
        self.num_carts = sum([1 if unit.is_cart() else 0 for unit in player.units])
        self.num_city_tiles = player.city_tile_count
        self.num_opponent_workers = sum([1 if unit.is_worker() else 0 for unit in opponent.units])
        self.num_opponent_carts = sum([1 if unit.is_cart() else 0 for unit in opponent.units])
        self.num_opponent_city_tiles = opponent.city_tile_count
        self.research_points = player.research_points
        self.opponent_research_points = opponent.research_points
        self.turn = game_state.turn
        
    def get_state_vector(self):
        return np.array([
            self.num_workers,
            self.num_carts,
            self.num_city_tiles,
            self.num_opponent_workers,
            self.num_opponent_carts,
            self.num_opponent_city_tiles,
            self.research_points,
            self.opponent_research_points,
            self.turn
        ]).reshape(1, -1)
        

class Controller:
    def __init__(self, game_state, player, opponent, debug):
        self.debug = debug
        self.game_state = game_state
        self.map = game_state.map
        self.state = State(game_state, player, opponent)
        self.player = player
        self.opponent = opponent
        self.mines = Mines(game_state, debug)
        self.workers = Workers([unit for unit in player.units if unit.is_worker()], self.mines, debug)
#         self.carts = []
        self.cities = CitiesWrapper(self.player.cities.values(), debug)
        
    def update(self, game_state, player, opponent):
        self.game_state = game_state
        self.state._update_state(game_state, player, opponent)
        self.map = game_state.map
        self.player = player
        self.opponent = opponent
        self.mines.update(player)
        self.cities.update(self.player.cities.values())
        self.workers.update(self.mines, [unit for unit in player.units if unit.is_worker()])
        
    def get_state_vector(self):
        return self.state.get_state_vector()
    
    def apply_agent_action(self, action):
        self.workers.update_task_proportions(action)    
        
    def get_actions(self):
        if self.debug:
            print("Turn", self.game_state.turn, file=sys.stderr)
        worker_actions = self.workers.get_actions(self)
        city_actions = self.cities.get_actions(self)
        return worker_actions + city_actions
