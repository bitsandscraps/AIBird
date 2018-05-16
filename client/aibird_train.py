""" Train AIBird agent using PPO """
#import numpy as np
import tensorflow as tf

from baselines import bench, logger
#from baselines.a2c.utils import fc
#from baselines.common.distributions import make_pdtype

import aibird_env

MAX_ACTION = [50, 90, 4]
MIN_ACTION = [5, -90, 0.1]

def train(penv, num_timesteps, seed):
    """ Slight modification of train method in baselines.ppo2.run_mujoco """
    from baselines.common import set_global_seeds
    from baselines.common.vec_env.vec_normalize import VecNormalize
    from baselines.ppo2 import ppo2
    from baselines.common.vec_env.dummy_vec_env import DummyVecEnv
    from baselines.ppo2.policies import CnnPolicy
    ncpu = 3
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    tf.Session(config=config).__enter__()
    def make_env():
        env = bench.Monitor(penv, logger.get_dir())
        return env
    env = DummyVecEnv([make_env])
    env = VecNormalize(env)

    set_global_seeds(seed)
    policy = CnnPolicy
    ppo2.learn(policy=policy, env=env, nsteps=2048, nminibatches=32,
               lam=0.95, gamma=0.99, noptepochs=10, log_interval=1,
               ent_coef=0.0,
               lr=3e-4,
               cliprange=0.2,
               total_timesteps=num_timesteps)

def clip_screenshot(img):
    return img[100:-1, :, :]    # Crop away unnecessary parts(the score part)

def main():
    """ Train AIBird agent using PPO
    """
    logger.configure()
    env = aibird_env.AIBirdEnv(MAX_ACTION, MIN_ACTION,)
    env.startup()
    train(env, int(1e6), 0)

if __name__ == "__main__":
    main()
