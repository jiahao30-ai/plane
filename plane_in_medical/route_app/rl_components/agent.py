"""
强化学习智能体
实现具体的RL算法
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from .environment import create_environment
from collections import deque    #双端队列,用于经验回收

class DQN(nn.Module):
    """
    深度Q网络
    """
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_size)
    
    def forward(self,x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)
    
class DQNAgent:
    """DQN智能体"""
    def __init__(self, state_size, action_size, lr=0.001):
        self.state_size = state_size
        self.action_size = action_size
        #经验回收缓冲区,最大容量10000
        self.memory = deque(maxlen=50000)
        #当前探索率
        self.epsilon = 1.0  # 探索率
        #最小探索率
        self.epsilon_min = 0.01
        #探索率衰减因子
        self.epsilon_decay = 0.995
        self.learning_rate = lr
        
        # 神经网络,主Q网络，用于动作选择
        self.q_network = DQN(state_size, action_size)
        #目标网络，用于目标Q值计算
        self.target_network = DQN(state_size, action_size)
        #优化器，使用Adam优化算法
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)
        
        # 更新目标网络
        self.update_target_network()
        
    def update_target_network(self):
        """更新目标网络"""
        self.target_network.load_state_dict(self.q_network.state_dict())
        
    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state):
        """选择动作"""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.cpu().data.numpy())
    
    def replay(self, batch_size=32):
        """经验回放"""
        if len(self.memory) < batch_size:
            return
            
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (0.99 * next_q_values * ~dones)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


