""" Train AIBird agent using PPO """
import datetime
import multiprocessing
import os
import sys
import subprocess
from socket import timeout
from time import sleep

import tensorflow as tf

# from skimage.color import rgb2grey
from skimage.transform import rescale

from baselines import logger
from baselines.bench import Monitor
from baselines.common import set_global_seeds
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.ppo2 import ppo2
from baselines.ppo2.policies import CnnPolicy
from aibird_subproc_vec_env import SubprocVecEnv

import aibird_env

MAX_ACTION = [80, 2.5]
MIN_ACTION = [-10, 0.1]

def make_aibird_env(envs, num_env, seed):
    def make_env(rank):
        def _thunk():
            env = Monitor(envs[rank],
                          logger.get_dir() and os.path.join(logger.get_dir(), str(rank)))
            return env
        return _thunk
    set_global_seeds(seed)
    return SubprocVecEnv([make_env(i) for i in range(num_env)])

def train(envs, num_env, num_timesteps, seed, load_path=None):
    """ Slight modification of train method in baselines.ppo2.run_mujoco """
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin':
        ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    with tf.Session(config=config) as _:
        env = VecFrameStack(make_aibird_env(envs, num_env, seed), 1)
        try:
            ppo2.learn(policy=CnnPolicy, env=env, nsteps=256, nminibatches=8,
                       lam=0.95, gamma=1, noptepochs=4, log_interval=1,
                       ent_coef=.01,
                       lr=lambda f: f * 2.5e-4,
                       cliprange=lambda f: f * 0.1,
                       total_timesteps=int(num_timesteps * 1.1),
                       save_interval=1, load_path=load_path)
        except timeout:
            # Kill chrome and server
            print(datetime.datetime.now().isoformat(), "Chrome crashed. Restarting....", flush=True)
            tf.reset_default_graph()
            env.close()
            for e in envs:
                e.terminate()
            return True
        except Exception as exception:
            env.close()
            for e in envs:
                e.terminate()
            raise exception
        return False

def process_screensot(img):
    """Crop away unnecessary parts(the score part)"""
    cimg = img[100:-1, :, :]
    return rescale(cimg, 0.5)

def quantize(act):
    """ 60 actions : 12 angle actions * 5 tap time actions """
    nangle = act % 12
    ntap = (act // 12) + 1
    tangle = nangle / 12
    ttap = ntap / 5
    angle = tangle * MAX_ACTION[0] + (1 - tangle) * MIN_ACTION[0]
    tap = ttap * MAX_ACTION[1] + (1 - ttap) * MIN_ACTION[1]
    return angle, tap

# def killserver():
#     """ Kill AIBirdServer """
#     print('killserver')
#     output = subprocess.run("jps", stdout=subprocess.PIPE).stdout
#     for line in ''.join(map(chr, output)).rstrip('\n').split('\n'):
#         if len(line) == 2:
#             pid, name = line.split()
#             if name == 'AIBirdServer':
#                 psutil.Process(int(pid)).terminate()
#     subprocess.run("jps")

def prepare_env(server_path, chrome_user, client_port):
    print('Preparing env', chrome_user, client_port)
    with open('log/chrome{}.error'.format(chrome_user), 'a') as chrome_error:
        chrome = subprocess.Popen(['google-chrome-stable', 'chrome.angrybirds.com',
                                   '--profile-directory=Profile {}'.format(chrome_user)],
                                  stderr=chrome_error)
    sleep(10)
    with open('log/server{}.log'.format(chrome_user), 'a') as server_log:
        server = subprocess.Popen(["ant", "run", "-Dproxyport={}".format(8999 + chrome_user),
                                   "-Dclientport={}".format(client_port)],
                                  cwd=server_path, stdout=server_log)
    sleep(10)
    return chrome, server

def main(start_level=1):
    """ Train AIBird agent using PPO
    """
    logger.configure('aibird_log_multi')
    curr_dir_path = os.path.dirname(os.path.realpath(__file__))
    server_path = os.path.abspath(os.path.join(curr_dir_path, os.pardir, 'server'))
    # find the newest checkpoint
    checkdir = os.path.join(logger.get_dir(), 'checkpoints')
    load_path = None
    if os.path.isdir(checkdir):
        checkpoints = [os.path.join(checkdir, f) for f in os.listdir(checkdir)]
        load_path = max(checkpoints, key=os.path.getctime)
    done = False
    while not done:
        # run chrome and AIBirdServer
        env = []
        for i in range(1, 5):
            ienv = aibird_env.AIBirdEnv(
                action_space=60, act_cont=False,
                process_state=process_screensot, process_action=quantize, start_level=start_level)
            ienv.startup(server_path=server_path, chrome_user=i, client_port=2000+i)
            env.append(ienv)
        # train
        done = train(env, 4, int(1e6), 0, load_path)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    else:
        main(int(sys.argv[1]))
