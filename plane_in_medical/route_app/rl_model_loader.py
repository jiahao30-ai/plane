"""
负责加载和初始化已训练的强化学习模型。
"""

import os
import json
from pathlib import Path
import torch
import numpy as np

# 导入你的 RL 组件
from route_app.rl_components.agent import DQNAgent
from route_app.rl_components.environment import create_environment
from route_app.rl_components.states import state_space

# 全局变量存储模型和环境
loaded_agent = None
loaded_env = None
# 如果状态构建需要医院数据模板
hospital_data_template = None 

def load_model_and_environment():
    """
    加载训练好的模型和创建环境实例。
    这个函数应该在 Django 应用启动时调用一次，或者在首次需要时懒加载。
    """
    global loaded_agent, loaded_env, hospital_data_template

    if loaded_agent is not None and loaded_env is not None:
        # 如果已经加载，则直接返回
        return loaded_agent, loaded_env

    # --- 1. 确定文件路径 ---
    base_dir = Path(__file__).resolve().parent.parent # plane_in_medical/route_app -> plane_in_medical
    data_dir = base_dir / 'data'
    model_path = data_dir / 'prepared' / 'dqn_full_checkpoint.pth'
    hospitals_file = data_dir / 'hospitals.json' # 需要最新的医院数据

    # --- 2. 加载医院数据 ---
    if not hospitals_file.exists():
        raise FileNotFoundError(f"医院数据文件未找到: {hospitals_file}")
    with open(hospitals_file, 'r', encoding='utf-8') as f:
        hospital_data_template = json.load(f)
    print(f"已加载 {len(hospital_data_template)} 家医院的数据。")

    # --- 3. 创建环境 (使用医院数据模板) ---
    # 注意：环境内部会复制医院数据，所以这里传入模板即可
    loaded_env = create_environment(hospital_data_template)
    print("已创建强化学习环境。")

    # --- 4. 初始化智能体 ---
    # 从环境获取 state_size 和 action_size
    # 注意：这里假设你的 state_size 是固定的，或者可以通过某种方式确定
    # 如果 state_size 是动态的或依赖于环境初始化，你可能需要调整
    # 一种方法是在训练脚本中保存 state_size 和 action_size
    # 这里我们假设可以从环境或 state_space 获取
    
    # 尝试从环境或 state_space 获取维度
    state_size = state_space.state_dimensions # 使用 states.py 中定义的维度
    action_size = loaded_env.action_space.action_size

    # 创建 DQNAgent 实例，学习率等参数在推理时通常不重要
    loaded_agent = DQNAgent(state_size, action_size, lr=1e-4) # lr 可以是任意值，因为不训练
    print(f"已初始化 DQN 智能体 (state_size={state_size}, action_size={action_size})。")

    # --- 5. 加载模型权重 ---
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件未找到: {model_path}")

    try:
        checkpoint = torch.load(model_path, map_location=torch.device('cpu')) # 使用 CPU 加载
        loaded_agent.q_network.load_state_dict(checkpoint['q_state_dict'])
        # loaded_agent.target_network.load_state_dict(checkpoint['target_state_dict']) # 推理时通常不需要
        loaded_agent.q_network.eval() # 设置为评估模式，关闭 dropout/batchnorm 等
        print(f"已从 {model_path} 加载模型权重。")
    except Exception as e:
        print(f"加载模型权重失败: {e}")
        raise

    return loaded_agent, loaded_env

if __name__ == "__main__":
    # 测试加载模型和创建环境
    agent, env = load_model_and_environment()
    print(f"加载的智能体: {agent}")
    print(f"加载的环境: {env}")

    """
    已加载 70 家医院的数据。
    已创建强化学习环境。
    已初始化 DQN 智能体 (state_size=36, action_size=73)。
    已从 E:\PycharmProjects\plane_in_medical\plane_in_medical\data\prepared\dqn_full_checkpoint.pth 加载模型权重。
    加载的智能体: <rl_components.agent.DQNAgent object at 0x0000017702A07320>
    加载的环境: <rl_components.environment.DroneDeliveryEnvironment object at 0x0000017702A07380>
    """