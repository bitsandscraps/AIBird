""" Train AIBird agent using PPO """
import multiprocessing
import os
import sys
import subprocess
from socket import timeout
from time import sleep

import psutil
import numpy as np
import tensorflow as tf

# from skimage.color import rgb2grey
from skimage.transform import rescale

from baselines import bench, logger

import aibird_env

MAX_ACTION = [90, 2.5]
MIN_ACTION = [-90, 0.1]

def train(penv, num_timesteps, seed, load_path=None):
    """ Slight modification of train method in baselines.ppo2.run_mujoco """
    from baselines.common import set_global_seeds
    from baselines.common.vec_env.vec_normalize import VecNormalize
    from baselines.ppo2 import ppo2
    from baselines.common.vec_env.dummy_vec_env import DummyVecEnv
    from baselines.ppo2.policies import CnnPolicy
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin':
        ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    with tf.Session(config=config) as _:
        def make_env():
            env = bench.Monitor(penv, logger.get_dir())
            return env
        env = DummyVecEnv([make_env])
        env = VecNormalize(env)

        set_global_seeds(seed)
        ppo2.learn(policy=CnnPolicy, env=env, nsteps=128, nminibatches=4,
                   lam=0.95, gamma=1, noptepochs=4, log_interval=1,
                   ent_coef=.01,
                   lr=lambda f: f * 2.5e-4,
                   cliprange=lambda f: f * 0.1,
                   total_timesteps=int(num_timesteps * 1.1),
                   save_interval=2, load_path=load_path)

def process_screensot(img):
    """Crop away unnecessary parts(the score part)"""
    cimg = img[100:-1, :, :]
    return rescale(cimg, 0.5)

def killserver():
    """ Kill AIBirdServer """
    output = subprocess.run("jps", stdout=subprocess.PIPE).stdout
    for line in ''.join(map(chr, output)).rstrip('\n').split('\n'):
        pid, name = line.split()
        if name == 'AIBirdServer':
            psutil.Process(int(pid)).terminate()
            return


def main():
    """ Train AIBird agent using PPO
    """
    logger.configure('aibird_log')
    curr_dir_path = os.path.dirname(os.path.realpath(__file__))
    server_path = os.path.abspath(os.path.join(curr_dir_path, os.pardir, 'server'))
    while True:
        try:
            # find the newest checkpoint
            checkdir = os.path.join(logger.get_dir(), 'checkpoints')
            checkpoints = [os.path.join(checkdir, f) for f in os.listdir(checkdir)]
            load_path = max(checkpoints, key=os.path.getctime)
            # run chrome and AIBirdServer
            with open('chrome.error', 'a') as chrome_error:
                chrome = subprocess.Popen(["google-chrome-stable", "chrome.angrybirds.com"],
                                          stderr=chrome_error)
            sleep(10)
            with open('server.log', 'a') as server_log, open('server.error', 'a') as server_error:
                subprocess.Popen(["ant", "run"], cwd=server_path,
                                 stdout=server_log, stderr=server_error)
            sleep(10)
            # train
            env = aibird_env.AIBirdEnv(
                np.asarray(MAX_ACTION), np.asarray(MIN_ACTION), process_screensot)
            env.startup()
            train(env, int(1e6), 0, load_path)
        except timeout:
            # Kill chrome and server
            tf.reset_default_graph()
            chrome.kill()
            killserver()

if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        killserver()
        raise exception
