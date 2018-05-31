""" An OpenAI environment interface for AIBird client """
    
from time import sleep
import subprocess

import numpy as np
from scipy.stats import logistic
import gym
import gym.spaces

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

    def __init__(self, action_space, act_cont,
                 process_state=lambda x: x, process_action=None, start_level=1):
        self.observation_space = None
        self.chrome = None
        self.server = None
        self.aibird_client = None
        self.server_path = None
        self.chrome_user = None
        self.client_port = None
        self.reset_count = 0
        self.start_level = start_level
        if act_cont:
            self.action_space = gym.spaces.Box(
                low=action_space[0], high=action_space[1], dtype=np.float64)
        else:
            self.action_space = gym.spaces.Discrete(action_space)
        self.action_count = 0
        self._process_state = process_state
        if process_action is None:
            def sigmoid(paction):
                """ Rescale (-infty, infty) to [-lower_bound, upper_bound] """
                action = []
                for act, amin, amax in zip(paction, action_space[0], action_space[1]):
                    scale = amax - amin
                    action.append(logistic.cdf(act) * scale + amin)
                return np.asarray(action)
            self._process_action = sigmoid
        else:
            self._process_action = process_action

    def startup(self, server_path, chrome_user, client_port):
        """Setups the AIBird client. Must be called before anything else.
        """
        self.chrome, self.server = prepare_env(server_path, chrome_user, client_port)
        self.server_path = server_path
        self.chrome_user = chrome_user
        self.client_port = client_port
        self.aibird_client = aibird_client.AIBirdClient(port=client_port)
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
            sleep(0.1)
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
        self.reset_count += 1
        if self.reset_count > 50:
            # Regularly restarts the server
            self.restart(True)
            self.reset_count = 0
        self.aibird_client.current_level = self.start_level
        self.action_count = 0
        return self._get_state()

    def terminate(self, weak=False):
        """ Terminate chrome and server. """
        self.aibird_client.disconnect()
        sleep(1)
        if not weak:
            self.chrome.terminate()
        self.server.terminate()

    def restart(self, weak=False):
        """ Restart chrome and server. """
        self.terminate(weak)
        sleep(5)
        if weak:
            self.server = prepare_env(self.server_path, self.chrome_user, self.client_port, prepare_chrome=False)[1]
        else:
            self.chrome, self.server = prepare_env(self.server_path, self.chrome_user, self.client_port)
        self.aibird_client = aibird_client.AIBirdClient(port=self.client_port)
        self.aibird_client.connect()

def prepare_env(server_path, chrome_user, client_port, prepare_chrome=True):
    chrome = None
    if prepare_chrome:
        with open('log/chrome{}.error'.format(chrome_user), 'a') as chrome_error:
            chrome = subprocess.Popen(['google-chrome-stable', 'chrome.angrybirds.com',
                                       '--profile-directory=Profile {}'.format(chrome_user)],
                                      stdout=chrome_error, stderr=chrome_error)
    sleep(10)
    with open('log/server{}.log'.format(chrome_user), 'a') as server_log:
        server = subprocess.Popen(["ant", "run", "-Dproxyport={}".format(8999 + chrome_user),
                                   "-Dclientport={}".format(client_port)],
                                  cwd=server_path, stdout=server_log)
    sleep(10)
    return chrome, server

