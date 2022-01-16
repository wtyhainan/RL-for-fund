
import gym
from gym import spaces
import numpy as np


class FundEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array'],
                'video.frames_per_second': 2}

    def __init__(self):
        self.action_space = None
        self.observation_space = None
        pass

    def step(self, action):
        # return self.state, reward, done, info
        return None

    def reset(self):
        # return self.state
        return None

    def render(self, mode='human'):
        return None

    def close(self):
        return None

