"""Plot DQN training logs (avg_reward, success_rate) and save PNG/CSV.

Usage (from project root):
  python -m plane_in_medical.route_app.rl_components.plot_training
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    root = Path(__file__).resolve().parents[3]
    data_dir = root / 'plane_in_medical' / 'data' / 'prepared'
    log_file = data_dir / 'dqn_full_log.json'
    out_png = data_dir / 'dqn_full_plot.png'
    out_csv = data_dir / 'dqn_full_log.csv'

    if not log_file.exists():
        print('Log file not found:', log_file)
        return 2

    with log_file.open('r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print('Empty log file')
        return 3

    steps = [int(x.get('step', i)) for i, x in enumerate(data)]
    avg_reward = [float(x.get('avg_reward', 0.0)) for x in data]
    success_rate = [float(x.get('success_rate', 0.0)) for x in data]
    epsilon = [float(x.get('epsilon', 0.0)) for x in data]

    # save CSV
    try:
        import csv
        with out_csv.open('w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            writer.writerow(['step', 'avg_reward', 'success_rate', 'epsilon'])
            for s, r, sr, e in zip(steps, avg_reward, success_rate, epsilon):
                writer.writerow([s, r, sr, e])
    except Exception as e:
        print('Failed to save CSV:', e)

    # plot
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(steps, avg_reward, color='tab:blue', label='avg_reward')
    ax1.set_xlabel('step')
    ax1.set_ylabel('avg_reward', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.plot(steps, success_rate, color='tab:green', label='success_rate')
    ax2.set_ylabel('success_rate', color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    # optionally plot epsilon as dotted on ax1
    ax1.plot(steps, epsilon, color='tab:red', linestyle='--', label='epsilon')

    # legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.title('DQN training: avg_reward & success_rate')
    plt.tight_layout()
    try:
        fig.savefig(out_png)
        print('Saved plot to', out_png)
    except Exception as e:
        print('Failed to save plot:', e)
        return 4

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
