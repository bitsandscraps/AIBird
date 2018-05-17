""" Train AIBird agent using PPO """
import multiprocessing
import sys

import numpy as np
import tensorflow as tf

# from skimage.color import rgb2grey
from skimage.transform import rescale

from baselines import bench, logger

import aibird_env

MAX_ACTION = [90, 2.5]
MIN_ACTION = [-90, 0.1]

def train(penv, num_timesteps, seed):
    """ Slight modification of train method in baselines.ppo2.run_mujoco """
    from baselines.common import set_global_seeds
    from baselines.common.vec_env.vec_normalize import VecNormalize
    from baselines.ppo2 import ppo2
    from baselines.common.vec_env.dummy_vec_env import DummyVecEnv
    from baselines.ppo2.policies import CnnPolicy
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin': ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    tf.Session(config=config).__enter__()
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
               save_interval=2)

def process_screensot(img):
    """Crop away unnecessary parts(the score part)"""
    cimg = img[100:-1, :, :]
    return rescale(cimg, 0.5)

def main():
    """ Train AIBird agent using PPO
    """
    logger.configure(dir='aibird_log')
    env = aibird_env.AIBirdEnv(
        np.asarray(MAX_ACTION), np.asarray(MIN_ACTION), process_screensot)
    env.startup()
    train(env, int(1e6), 0)

if __name__ == "__main__":
    main()
