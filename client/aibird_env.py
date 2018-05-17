""" An OpenAI environment interface for AIBird client """
import time

import gym
import numpy as np
from scipy.stats import logistic

import aibird_client

BIRD_ORDER = [  # Level
    'rrr',      # 1
    'rrrrr',    # 2
    'rrrr',     # 3
    'rrrr',     # 4
    'rrrr',     # 5
    'rrrr',     # 6
    'rrrr',     # 7
    'rrrr',     # 8
    'rrrr',     # 9
    'bbbbb',    # 10
    'rbbb',     # 11
    'bbbr',     # 12
    'bbrr',     # 13
    'rrrr',     # 14
    'bbbb',     # 15
    'yyyyy',    # 16
    'yyy',      # 17
    'yyyyy',    # 18
    'byyr',     # 19
    'yyyyy',    # 20
    'brybryyy'  # 21
    ]

MAXACTIONS = [3, 5, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4, 4, 4, 5, 3, 5, 4, 5, 8]

class AIBirdEnv(gym.Env):
    """OpenAI Environment for AIBird

    Args
    max_action, min_action -- numpy array holding the values
    process_state -- function for preprocessing state
                     default value: do nothing
    process_action -- function for processing action
                      default value: map (-infty, infty) to action space via sigmoid
    """

    def __init__(self, max_action, min_action,
                 process_state=lambda x: x, process_action=None):
        self.aibird_client = aibird_client.AIBirdClient()
        self.observation_space = None
        self.action_space = gym.spaces.Box(low=min_action, high=max_action, dtype=np.float64)
        self.action_count = 0
        self._process_state = process_state
        if process_action is None:
            def sigmoid(paction):
                """ Rescale (-infty, infty) to [-lower_bound, upper_bound] """
                action = []
                for act, amin, amax in zip(paction, min_action, max_action):
                    scale = amax - amin
                    action.append(logistic.cdf(act) * scale + amin)
                return np.asarray(action)
            self._process_action = sigmoid
        else:
            self._process_action = process_action

    def startup(self):
        """Setups the AIBird client. Must be called before anything else.
        """
        self.aibird_client.connect()
        screenshot = self._get_state()
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=screenshot.shape, dtype=screenshot.dtype)

    def _get_state(self):
        """ Get screenshot from AIBird Client and process it. """
        return self._process_state(self.aibird_client.screenshot)

    def step(self, action):
        """Executes `action` and returns the reward. """
        level = self.aibird_client.current_level
        score = self.aibird_client.current_score
        is_last_shot = self.action_count == (MAXACTIONS[level - 1] - 1)
        processed_action = self._process_action(action)
        reward = self.aibird_client.polar_shoot(*processed_action)
        self.action_count += 1
        level_over = self.aibird_client.is_level_over
        observation = self._get_state()
        if not (is_last_shot or level_over):
            # Both birds and pigs are left
            return observation, reward, False, dict()
        state = self.aibird_client.state
        while level_over and not state.isover():
            time.sleep(0.1)
            state = self.aibird_client.state
        if state.won():
            reward = self.aibird_client.current_score - score
            if self.aibird_client.next_level():
                # Proceed to next level
                self.action_count = 0
                observation = self._get_state()
                return observation, reward, False, dict()
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
        self.aibird_client.current_level = 1
        self.action_count = 0
        return self._get_state()
