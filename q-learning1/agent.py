from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from Controller import Controller
from RLAgent import *

def calculate_reward(s, s_prime, reward_weights):
        reward_vec = (s_prime[0] - s[0]) * np.array(reward_weights)
        return np.sum(reward_vec)

# we declare this global game_state object so that state persists across turns so we do not need to reinitialize it all the time
game_state = None
controller = None
state = None
action_code = None
rl_agent = None
def agent(observation, configuration):
    global game_state
    global controller
    global state
    global action_code
    global rl_agent

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
        
        player = game_state.players[observation.player]
        opponent = game_state.players[(observation.player + 1) % 2]
        controller = Controller(game_state, player, opponent, False)
        state = controller.get_state_vector()
        
        rl_agent = RLAgent("test", do_explore=False, record_replays=False)
        action_code = 54
        reward = 0
    else:
        game_state._update(observation["updates"])
        player = game_state.players[observation.player]
        opponent = game_state.players[(observation.player + 1) % 2]
        controller.update(game_state, player, opponent)
    
        s_prime = controller.get_state_vector()
        reward = calculate_reward(state, s_prime, rl_agent.reward_weights)
        if rl_agent.record_replays:
            rl_agent.add_replay([list(state[0]), action_code, reward, list(s_prime[0]), game_state.turn == 359])
        state = s_prime
    
        action_code = rl_agent.get_action(state)
    action = rl_agent.lookup_action(action_code)
    print(action, state, reward)
    controller.apply_agent_action(action)  

    return controller.get_actions()
