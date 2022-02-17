import gym

from collections import deque

class QuadsTimeDelayWrapper(gym.Wrapper):
    def __init__(self, env, delay_steps=5):  # control frequency is 100Hz, so this is 50ms delay by default
        gym.Wrapper.__init__(env)
        self.obs_queue = deque([])
        self.delay_steps = delay_steps

    def step(self, action):
        obs, rewards, dones, infos = self.env.step(action)
        self.obs_queue.append(obs)
        delayed_obs = self.obs_queue.popleft()
        return delayed_obs, rewards, dones, infos


    def reset(self, **kwargs):
        obs = self.env.reset()
        self.obs_queue = deque([obs] * self.delay_steps)
        return obs