import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, Input, Reshape
from tensorflow.keras.optimizers import Adam
from RLAgent import *
from agent import *
from kaggle_environments import make

def train_agent(num_episodes):
    for i in range(num_episodes):
        env = make("lux_ai_2021", configuration={"loglevel": 1, "annotations": True}, debug=True)
        steps = env.run([agent, "simple_agent"])
        print("Episode", i + 1, "of", num_episodes, "completed")

agent_name = "test"
settings = {
    "gamma": 0.2,
    "epsilon": 0.1,
    "num_explore_turns": 5,
    "train_batch_size": 10,
    "train_interval": 60,
    "reward_weights": (1, 1, 1, -1, -1, -1, 0.2, -0.2, -0.5)
}

optimizer = Adam(learning_rate=0.2)
model = Sequential()
model.add(Dense(50, activation='relu', input_dim=9))
model.add(Dense(50, activation='relu'))
model.add(Dense(55, activation='linear'))
model.compile(loss='mse', optimizer=optimizer)

rl_agent = RLAgent(agent_name, settings, model)

train_agent(1)



