from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from Controller import Controller
import math
import sys

# we declare this global game_state object so that state persists across turns so we do not need to reinitialize it all the time
game_state = None
controller = None

def base_agent(observation, configuration):
    global game_state
    global controller

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
        
        player = game_state.players[observation.player]
        opponent = game_state.players[(observation.player + 1) % 2]
        controller = Controller(game_state, player, opponent, False)
        
    else:
        game_state._update(observation["updates"])
        player = game_state.players[observation.player]
        opponent = game_state.players[(observation.player + 1) % 2]
        controller.update(game_state, player, opponent)
    
    return controller.get_actions()
