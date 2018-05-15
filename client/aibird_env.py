""" An OpenAI environment interface for AIBird client """

import gym
import numpy as np

import aibird_client

MINR = 50
MAXR = 50
MINTHETA = -90
MAXTHETA = 90
MINTAPTIME = 0.1
MAXTAPTIME = 3
MAXACTIONS = [3, 5, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4, 4, 4, 5, 3, 5, 4, 5, 8]

class AIBirdEnv(gym.Env):
    """OpenAI Environment for AIBird"""

    def __init__(self):
        self.aibird_client = aibird_client.AIBirdClient()
        self.observation_space = None
        self.action_space = None
        self.meaningful_shot = [False] * 21
        self.action_count = 0

    def startup(self):
        """Setups the AIBird client. Must be called before anything else.
        """
        self.aibird_client.connect()
        screenshot = self.aibird_client.screenshot
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=screenshot.shape, dtype=screenshot.dtype)
        action_low = np.asarray([MINR, MINTHETA, MINTAPTIME])
        action_high = np.asarray([MAXR, MAXTHETA, MAXTAPTIME])
        self.action_space = gym.spaces.Box(low=action_low, high=action_high, dtype=np.float64)

    def step(self, action):
        """Executes `action` and returns the reward.
        """
        mode = 'safe'
        level = self.aibird_client.current_level
        score = self.aibird_client.current_score
        is_last_shot = self.action_count == (MAXACTIONS[level - 1] - 1)
        if ((self.action_count < MAXACTIONS[level - 1] - 1) and
                (not self.meaningful_shot[level - 1])):
            mode = 'fast'
        print(action)
        reward = self.aibird_client.polar_shoot(action[0], action[1], action[2], mode)
        self.action_count += 1
        if reward > 0:
            # Performed a meaningful shot. From next time use safe mode to get
            # accurate scores.
            self.meaningful_shot[level - 1] = True
        level_over = self.aibird_client.is_level_over
        observation = self.aibird_client.screenshot
        if not (is_last_shot or level_over):
            return observation, reward, False, dict()
        if self.aibird_client.state.won():
            reward = self.aibird_client.current_score - score
            if self.aibird_client.next_level():
                # Proceed to next level
                self.action_count = 0
                observation = self.aibird_client.screenshot
                return observation, reward, False, dict()
        # Either lost or won all levels
        print('Finished')
        return observation, reward, True, dict()

    def render(self, mode='human'):
        """ Since the actual AI Bird game is running, render is unnecessary.
        """
        return None

    def reset(self):
        """ Reset the game, i.e., load level 1.
        :returns: the screenshot of level 1
        """
        print("Reset")
        self.aibird_client.current_level = 1
        return self.aibird_client.screenshot
