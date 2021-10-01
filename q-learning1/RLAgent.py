from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import random
import pickle

from tensorflow import keras
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, Input, Reshape
from tensorflow.keras.optimizers import Adam
from pathlib import Path

class RLAgent:
    def __init__(self, agent_name, settings=None, model=None, do_explore=True, record_replays=True):
        self.agent_name = agent_name
        self.do_explore = do_explore
        self.record_replays = record_replays
        
        if settings is None:
            with open(self.agent_name + "_settings", "rb") as settings_file:
                settings = pickle.load(settings_file)
        else:
            with open(self.agent_name + "_settings", "wb") as settings_file:
                pickle.dump(settings, settings_file)
                
        if model is not None:
            model.save(agent_name + "_model")
                
        self.action_space = self._get_action_space()
        self.experience_replay = []
        self.state_size = 9
        self.action_size = len(self.action_space)
        self.train_batch_size = settings["train_batch_size"]
        self.train_interval = settings["train_interval"]
        self.gamma = settings["gamma"]
        self.epsilon = settings["epsilon"]
        self.reward_weights = settings["reward_weights"]
        self.num_explore_turns = settings["num_explore_turns"]
        self.explore_timer = 0
        self.exploring = False
        self.explore_action = None
        self.q_net = keras.models.load_model(self.agent_name + "_model")
        self.target_net = self.q_net
        
    def _get_action_space(self):
        action_space = []
        for i in range(10):
            for j in range(10 - i):
                a, b = i / 10.0, j / 10.0
                c = (10 - i - j) / 10.0
                action_space.append([a, b, c])
                    
        return action_space
    
    def get_action(self, state):
        if self.exploring:
            self.explore_timer -= 1
            if self.explore_timer == 0:
                self.exploring = False
#                 print("Ending exploration")
            return self.explore_action
        
        if self.do_explore and np.random.rand() < self.epsilon:
#             print("Starting exploration")
            self.exploring = True
            self.explore_timer = self.num_explore_turns
            self.explore_action = random.randrange(self.action_size)
            return self.explore_action

        q_vals = self.q_net.predict(state)
        return np.argmax(q_vals[0])
    
    def lookup_action(self, code):
        return self.action_space[code]
    
    def train(self, batch_size):
        replays = []
        with open(self.agent_name + "_replays", "rb") as replay_file:
            replays = pickle.load(replay_file)

        for replay in replays:
            replay[0] = np.array(replay[0]).reshape(1, -1)
            replay[3] = np.array(replay[3]).reshape(1, -1)
        replay_sample = random.sample(replays, batch_size)
        
        for state, action, reward, next_state, last_turn in replay_sample:
            target = self.q_net.predict(state)
            
            if last_turn:
                target[0][action] = reward
            else:
                t = self.target_net.predict(next_state)
                target[0][action] = reward + self.gamma * np.amax(t[0])
            
            self.q_net.fit(state, target, epochs=1, verbose=0)
        self.q_net.save(self.agent_name + "_model")
    
    def add_replay(self, replay):
        replays = []
        with open(self.agent_name + "_replays", "rb") as replay_file:
            replays = pickle.load(replay_file)
        with open(self.agent_name + "_replays", "wb") as replay_file:
            replays.append(replay)
            pickle.dump(replays, replay_file)

