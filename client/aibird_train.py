""" Train AIBird agent using PPO """
import datetime
import multiprocessing
import os
import sys
from socket import timeout
import subprocess
import psutil

import tensorflow as tf

# from skimage.color import rgb2grey
from skimage.transform import rescale

from baselines import bench, logger
from baselines.common import set_global_seeds
from baselines.ppo2 import ppo2
from baselines.ppo2.policies import CnnPolicy

import aibird_env

MAX_ACTION = [80, 2.5]
MIN_ACTION = [-10, 0.1]

def train(penv, num_timesteps, seed, load_path=None):
    """ Slight modification of train method in baselines.ppo2.run_mujoco """
    from baselines.common.vec_env.dummy_vec_env import DummyVecEnv
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin':
        ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    def make_env():
        env = bench.Monitor(penv, logger.get_dir(), allow_early_resets=True)
        return env
    set_global_seeds(seed)
    with tf.Session(config=config) as _:
        env = DummyVecEnv([make_env])
        ppo2.learn(policy=CnnPolicy, env=env, nsteps=128, nminibatches=4,
                   lam=0.95, gamma=1, noptepochs=10, log_interval=1,
                   ent_coef=.01,
                   lr=lambda f: f * 2.5e-4,
                   cliprange=lambda f: f * 0.1,
                   total_timesteps=int(num_timesteps * 1.1),
                   save_interval=1, load_path=load_path)

def process_screensot(img):
    """Crop away unnecessary parts(the score part)"""
    cimg = img[100:-1, :, :]
    return rescale(cimg, 0.5)

def quantize(act):
    """ 60 actions : 12 angle actions * 5 tap time actions """
    nangle = (act % 12) + 1
    ntap = (act // 12) + 1
    tangle = nangle / 12
    ttap = ntap / 5
    angle = tangle * MAX_ACTION[0] + (1 - tangle) * MIN_ACTION[0]
    tap = ttap * MAX_ACTION[1] + (1 - ttap) * MIN_ACTION[1]
    return angle, tap

def killserver():
    """ Kill AIBirdServer """
    output = subprocess.run("jps", stdout=subprocess.PIPE).stdout
    print(output)
    for line in ''.join(map(chr, output)).rstrip('\n').split('\n'):
        splitted = line.split()
        if len(splitted) == 2:
            pid, name = splitted
            if name == 'AIBirdServer':
                psutil.Process(int(pid)).terminate()
    subprocess.run("jps")

def main():
    """ Train AIBird agent using PPO
    """
    logger.configure('aibird_log_1to6')
    curr_dir_path = os.path.dirname(os.path.realpath(__file__))
    server_path = os.path.abspath(os.path.join(curr_dir_path, os.pardir, 'server'))
    # find the newest checkpoint
    checkdir = os.path.join(logger.get_dir(), 'checkpoints')
    load_path = None
    if os.path.isdir(checkdir):
        checkpoints = [os.path.join(checkdir, f) for f in os.listdir(checkdir)]
        load_path = max(checkpoints, key=os.path.getctime)
    while True:
        try:
            env = aibird_env.AIBirdEnv(
                action_space=60, act_cont=False,
                process_state=process_screensot, process_action=quantize)
            env.startup(server_path, 1, 2000)
            train(env, int(1e6), 0, load_path)
        except timeout:
            # Kill chrome and server
            print(datetime.datetime.now().isoformat(), "Chrome crashed. Restarting....", flush=True)
            tf.reset_default_graph()
            env.restart()
            killserver()
        except:
            env.terminate()
            killserver()
            raise

if __name__ == "__main__":
    main()
