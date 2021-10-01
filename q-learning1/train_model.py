import sys
from RLAgent import *
from agent import *
from base_agent import base_agent
from kaggle_environments import make

def run_matches(num_matches):
    for i in range(num_matches):
        env = make("lux_ai_2021", configuration={"seed": 562124210, "loglevel": 1, "annotations": True}, debug=True)
        steps = env.run([agent, base_agent])
        print("Match", i + 1, "of", num_matches, "completed")
def train_agent(num_sessions, batch_size):
    rl_agent = RLAgent("test")
    for i in range(num_sessions):
        rl_agent.train(batch_size)
        print("Training session", i + 1, "of", num_sessions, "completed")

num_matches = int(sys.argv[1])
num_sessions = int(sys.argv[2])
batch_size = int(sys.argv[3])
run_matches(num_matches)
train_agent(num_sessions, batch_size)