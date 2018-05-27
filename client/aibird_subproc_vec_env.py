from multiprocessing import Process, Pipe
from socket import timeout
import numpy as np
from baselines.common.vec_env import VecEnv, CloudpickleWrapper

SUCCESS = 0
FAILURE = -1


def worker(remote, parent_remote, env_fn_wrapper):
    parent_remote.close()
    env = env_fn_wrapper.x()
    try:
        while True:
            cmd, data = remote.recv()
            if cmd == 'step':
                ob, reward, done, info = env.step(data)
                if done:
                    ob = env.reset()
                remote.send((SUCCESS, ob, reward, done, info))
            elif cmd == 'reset':
                ob = env.reset()
                remote.send((SUCCESS, ob))
            elif cmd == 'reset_task':
                ob = env.reset_task()
                remote.send((SUCCESS, ob))
            elif cmd == 'close':
                remote.close()
                break
            elif cmd == 'get_spaces':
                remote.send((SUCCESS, env.observation_space, env.action_space))
            else:
                raise NotImplementedError
    except timeout:
        remote.send((FAILURE,))
        remote.close()


class SubprocVecEnv(VecEnv):
    def __init__(self, env_fns, spaces=None):
        """
        envs: list of gym environments to run in subprocesses
        """
        self.waiting = False
        self.closed = False
        nenvs = len(env_fns)
        self.remotes, self.work_remotes = zip(*[Pipe() for _ in range(nenvs)])
        self.ps = [Process(target=worker, args=(work_remote, remote, CloudpickleWrapper(env_fn)))
                   for (work_remote, remote, env_fn)
                   in zip(self.work_remotes, self.remotes, env_fns)]
        for p in self.ps:
            p.daemon = True # if the main process crashes, we should not cause things to hang
            p.start()
        for remote in self.work_remotes:
            remote.close()

        self.remotes[0].send(('get_spaces', None))
        result = self.remotes[0].recv()
        if result[0] != SUCCESS:
            raise timeout
        _, observation_space, action_space = result
        VecEnv.__init__(self, len(env_fns), observation_space, action_space)

    def step_async(self, actions):
        for remote, action in zip(self.remotes, actions):
            remote.send(('step', action))
        self.waiting = True

    def step_wait(self):
        results = [remote.recv() for remote in self.remotes]
        self.waiting = False
        self._check_timeout(results)
        _, obs, rews, dones, infos = zip(*results)
        return np.stack(obs), np.stack(rews), np.stack(dones), infos

    def reset(self):
        for remote in self.remotes:
            remote.send(('reset', None))
        results = [remote.recv() for remote in self.remotes]
        self._check_timeout(results)
        _, obs = zip(*results)
        return np.stack(obs)

    def reset_task(self):
        for remote in self.remotes:
            remote.send(('reset_task', None))
        results = [remote.recv() for remote in self.remotes]
        self._check_timeout(results)
        _, obs = zip(*results)
        return np.stack(obs)

    def close(self):
        if self.closed:
            return
        if self.waiting:
            for remote in self.remotes:
                remote.recv()
        for remote in self.remotes:
            remote.send(('close', None))
        for p in self.ps:
            p.join()
        self.closed = True

    def _check_timeout(self, results):
        for result in results:
            if result[0] != SUCCESS:
                self.close()
                raise timeout
