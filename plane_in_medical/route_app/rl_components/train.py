import random
import json
from pathlib import Path
import time
import numpy as np
from .agent import DQNAgent
from .environment import create_environment
from ...utils.prepare_training_data import load_jsonl
import copy    #用于在评估时创建医院数据的深拷贝,确保评估过程不会影响训练环境


def evaluate(agent, env, hospitals_template, orders_subset, n_eval=100):
    """
    评估训练中智能体的性能
    参数:
        agent: 智能体对象
        env: 训练时使用的环境(此函数会创建新的评估环境,不直接使用这个)
        hospitals_template: 原始医院数据模版,用于创建评估环境
        orders_subset: 用于评估的订单子集
        n_eval: 评估的订单数量,默认100个
    """
    total_r = 0.0
    total_succ = 0
    n = min(n_eval, len(orders_subset))
    #使用hospitals_template的深拷贝,确保评估不会影响训练时的医院库存状态
    eval_hospitals = copy.deepcopy(hospitals_template)
    eval_env = create_environment(eval_hospitals)

    old_eps = getattr(agent, 'epsilon', None)
    if hasattr(agent, 'epsilon'):
        agent.epsilon = 0.0

    for i in range(n):
        order = orders_subset[i]
        state = eval_env.reset(order, order.get('items', []))
        action = agent.act(state)
        _, r, _, info = eval_env.step(action)
        total_r += float(r)

        sufficient = False
        if isinstance(info, dict):
            if info.get('sufficient') or info.get('sufficient_inventory') or info.get('decremented'):
                sufficient = True
            exec_res = info.get('execution_result') if info.get('execution_result') else info
            if isinstance(exec_res, dict):
                if exec_res.get('sufficient') or exec_res.get('sufficient_inventory') or exec_res.get('decremented'):
                    sufficient = True
                if exec_res.get('assignments'):
                    if len(exec_res.get('assignments')) > 0 and not exec_res.get('unfulfilled_items'):
                        sufficient = True

        if sufficient:
            total_succ += 1

    if old_eps is not None:
        agent.epsilon = old_eps
    #返回平均奖励和成功率
    return (total_r / n) if n > 0 else 0.0, (total_succ / n) if n > 0 else 0.0

def main():
    import argparse
    parser = argparse.ArgumentParser()
    #训练轮数,默认是10轮
    parser.add_argument('--epochs', type=int, default=10, help='number of full passes over the orders')
    #批量大小,默认是64
    parser.add_argument('--batch_size', type=int, default=128)
    #目标网络更新间隔,默认是1000步更新一次
    parser.add_argument('--target_update', type=int, default=2000)
    #评估间隔,默认是2000步评估一次
    parser.add_argument('--eval_interval_steps', type=int, default=2000)
    #随机种子
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    #项目根目录
    root = Path(__file__).resolve().parents[3]
    data_dir = root / 'plane_in_medical' / 'data'
    #订单数据路径
    orders_file = data_dir / 'data_pool_train.jsonl'
    #医院数据路径
    hospitals_file = data_dir / 'hospitals.json'

    orders = load_jsonl(orders_file)
    with open(hospitals_file, 'r', encoding='utf-8') as f:
        hospitals = json.load(f)
    #创建强化学习环境,传入医院数据
    env = create_environment(hospitals)

    sample_order = orders[0]
    state = env.reset(sample_order, sample_order.get('items', []))
    if isinstance(state, dict):
        state_size = env.state_space.state_dimensions
    else:
        try:
            state_size = len(state)
        except Exception:
            state_size = env.state_space.state_dimensions
    #获取动作空间大小
    action_size = env.action_space.action_size
    #创建DQN智能体,指定状态大小,动作大小和学习率
    agent = DQNAgent(state_size, action_size, lr=5e-4)
    #设置随机种子以确保实验可重现
    random.seed(args.seed)
    np.random.seed(args.seed)
    #当前训练步数
    n_steps = 0
    #训练日志
    log = []
    total_steps = args.epochs * len(orders)
    print(f'Training for {args.epochs} epochs over {len(orders)} orders ({total_steps} steps)')

    start = time.time()
    for epoch in range(args.epochs):
        random.shuffle(orders)
        """
        1.增加步数计数
        2.重置环境
        3.智能体选择动作
        4.执行动作并获取环境反馈
        5.存储经验到回收缓冲区
        6.进行经验回收训练
        """
        for order in orders:
            n_steps += 1
            state = env.reset(order, order.get('items', []))
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            agent.replay(args.batch_size)
            #定期更新目标网格参数
            if n_steps % args.target_update == 0:
                agent.update_target_network()
            #定期评估智能体性能并记录日志
            if n_steps % args.eval_interval_steps == 0:
                avg_r, avg_succ = evaluate(agent, env, hospitals, orders[:200], n_eval=100)
                print(f'[step {n_steps}] eval avg_reward={avg_r:.2f} success_rate={avg_succ:.2f} eps={agent.epsilon:.3f}')
                log.append({'step': n_steps, 'avg_reward': avg_r, 'success_rate': avg_succ, 'epsilon': agent.epsilon})
    #计算耗时时间
    elapsed = time.time() - start
    print('Training finished, elapsed=%.1fs' % elapsed)
    #保存训练日志
    outp = data_dir / 'prepared' / 'dqn_full_log.json'
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    try:
        import torch
        ckpt = {
            'q_state_dict': agent.q_network.state_dict(),
            'target_state_dict': agent.target_network.state_dict(),
        }
        torch.save(ckpt, str(data_dir / 'prepared' / 'dqn_full_checkpoint.pth'))
        print('Saved checkpoint to', str(data_dir / 'prepared' / 'dqn_full_checkpoint.pth'))
    except Exception:
        print('torch not available or save failed')


if __name__ == '__main__':
    main()
