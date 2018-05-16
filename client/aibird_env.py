""" An OpenAI environment interface for AIBird client """

import gym
import numpy as np
from scipy.stats import logistic
# from skimage.color import rgb2grey
# from skimage.transform import rescale

import aibird_client

ACTION_UPPER_BOUND = [50, 90, 4]
ACTION_LOWER_BOUND = [5, -90, 0.1]
MAXACTIONS = [3, 5, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4, 4, 4, 5, 3, 5, 4, 5, 8]

class AIBirdEnv(gym.Env):
    """OpenAI Environment for AIBird

    Args
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
        self.meaningful_shot = [False] * 21
        self.action_count = 0
        self._process_state = process_state
        if process_action is None:
            def sigmoid(paction):
                """ Rescale (-infty, infty) to [-lower_bound, upper_bound] """
                action = []
                for act, amin, amax in zip(paction, min_action, max_action):
                    mean = (amin + amax) / 2
                    scale = amax - amin
                    action.append(logistic.cdf(act, mean, scale))
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
        mode = 'safe'
        level = self.aibird_client.current_level
        score = self.aibird_client.current_score
        is_last_shot = self.action_count == (MAXACTIONS[level - 1] - 1)
        if ((self.action_count < MAXACTIONS[level - 1] - 1) and
                (not self.meaningful_shot[level - 1])):
            mode = 'fast'
        action = self._process_action(action)
        reward = self.aibird_client.polar_shoot(*action, mode)
        self.action_count += 1
        if reward > 0:
            # Performed a meaningful shot. From next time use safe mode to get
            # accurate scores.
            self.meaningful_shot[level - 1] = True
        level_over = self.aibird_client.is_level_over
        observation = self._get_state()
        if not (is_last_shot or level_over):
            return observation, reward, False, dict()
        if self.aibird_client.state.won():
            reward = self.aibird_client.current_score - score
            if self.aibird_client.next_level():
                # Proceed to next level
                self.action_count = 0
                observation = self._get_state()
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
        return self._get_state()
