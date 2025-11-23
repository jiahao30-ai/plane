"""
测试强化学习奖励函数的逻辑
验证在不同情况下奖励函数能否正确给出相对合理的奖励

两个核心原则:
库存优先原则：在距离相同的情况下，库存充足的医院应该比没有库存的医院获得更高的奖励
距离优先原则：在库存相同的情况下，距离更近的医院应该比距离较远的医院获得更高的奖励
"""
try:
    from .rewards import reward_function
except Exception:
    from rewards import reward_function


def test_near_and_instock_vs_no_stock():
    """
    当两个医院距离相同(都很近),但一个库存充足,另一个没有库存
    期望库存充足的医院应该获得更高的奖励
    """
    execution_result_good = {
        'action': 'select_hospital',
        'hospital': {'inventory_match': 1.0, 'distance': 1.0}
    }
    execution_result_bad = {
        'action': 'select_hospital',
        'hospital': {'inventory_match': 0.0, 'distance': 1.0}
    }
    r_good = reward_function.calculate_reward(None, None, None, execution_result_good)
    r_bad = reward_function.calculate_reward(None, None, None, execution_result_bad)
    print('r_good=', r_good, 'r_bad=', r_bad)
    assert r_good > r_bad, 'Expected near+instock reward > near+no-stock'


def test_near_instock_vs_far_instock():
    """
    当两个医院都有充足库存,但一个很近,另一个很远
    期望很近的医院应该获得更高的奖励
    """
    exec_near = {'action': 'select_hospital', 'hospital': {'inventory_match': 1.0, 'distance': 1.0}}
    exec_far = {'action': 'select_hospital', 'hospital': {'inventory_match': 1.0, 'distance': 50.0}}
    r_near = reward_function.calculate_reward(None, None, None, exec_near)
    r_far = reward_function.calculate_reward(None, None, None, exec_far)
    print('r_near=', r_near, 'r_far=', r_far)
    assert r_near > r_far, 'Expected near in-stock reward > far in-stock'


def run_all():
    test_near_and_instock_vs_no_stock()
    test_near_instock_vs_far_instock()
    print('All reward tests passed')


if __name__ == '__main__':
    run_all()


'''
运行结果:
      r_good= 196.0 r_bad= -404.0
      r_near= 196.0 r_far= 0.0
      All reward tests passed
      说明奖励方向性符合预期(近+有货得分高;无货严重惩罚)
'''