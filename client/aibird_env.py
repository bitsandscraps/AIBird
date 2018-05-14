""" An OpenAI environment interface for AIBird client """

import gym
import numpy as np

import aibird_client

MINR = 0
MAXR = 50
MINTHETA = -90
MAXTHETA = 90
MINTAPTIME = 0
MAXTAPTIME = 3

class AIBirdEnv(gym.Env):
    """OpenAI Environment for AIBird"""

    def __init__(self):
        self.aibird_client = aibird_client.AIBirdClient()

    def startup(self):
        """Setups the AIBird client. Must be called before anything else.
        """
        self.aibird_client.connect()
        screenshot = self.aibird_client.screenshot
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=screenshot.shape, dtype=screenshot.dtype)
        action_low = np.asarray([MINR, MINTHETA, MINTAPTIME])
        action_high = np.asarray([MAXR, MAXTHETA, MAXTAPTIME])
        self.action_space = gym.spaces.Box(low=action_low, high=action_high)

    def step(self, action):
        """Executes `action` and returns the reward.
        """
        reward = self.aibird_client.polar_shoot(action[0], action[1], action[2])
        level_over = self.aibird_client.is_level_over
        observation = self.aibird_client.screenshot
        if not level_over:
            return observation, reward, False, None
        if self.aibird_client.state.won():
            if self.aibird_client.next_level():
                # Proceed to next level
                observation = self.aibird_client.screenshot
                return observation, reward, False, None
        # Either lost or won all levels
        return observation, reward, True, dict()

    def render(self, mode='human'):
        """ Since the actual AI Bird game is running, render is unnecessary.
        """
        return None

    def reset(self):
        """ Reset the game, i.e., load level 1.
        :returns: the screenshot of level 1

        """
        self.aibird_client.level = 1
        return self.aibird_client.screenshot
