import numpy as np


class ScheduledOptim(object): #https://github.com/jefflai108/Contrastive-Predictive-Coding-PyTorch/blob/a9dab4e759aaa68dce1b1ada46a8035076ba3296/src/optimizer_v1.py#L24
    """A simple wrapper class for learning rate scheduling"""

    def __init__(self, optimizer, n_warmup_steps):
        self.optimizer = optimizer
        self.d_model = 128
        self.n_warmup_steps = n_warmup_steps
        self.n_current_steps = 0
        self.delta = 1

    def state_dict(self):
        return self.optimizer.state_dict()

    def load_state_dict(self, state_dict):
        self.optimizer.load_state_dict(state_dict)

    def step(self):
        """Step by the inner optimizer"""
        self.optimizer.step()

    def zero_grad(self):
        """Zero out the gradients by the inner optimizer"""
        self.optimizer.zero_grad()

    def increase_delta(self):
        self.delta *= 2

    def update_learning_rate(self):
        """Learning rate scheduling per step"""
        lr = 0.0
        for param_group in self.optimizer.param_groups:
            lr = param_group['lr']*0.5
            print('updating lr from', param_group['lr'], end=' ')
            break

        for param_group in self.optimizer.param_groups:
             param_group['lr'] = lr
        print('to', lr)
        return lr