from django.shortcuts import render
from django.http import JsonResponse
from pay_app.models import Order
# Create your views here.
from .models import Hospital
from django.contrib.auth.decorators import login_required
from utils.get_position import XiAnGeocoder
import json

from .rl_model_loader import load_model_and_environment
import torch
import numpy as np


@login_required
def get_route(request):
    """
    处理配送路径请求的视图。
    """
    if request.method == 'GET':
        try:
            print("用到了强化学习")
            # --- 1. 解析请求数据 ---
            order_id = request.GET.get('order_id')
            order = Order.objects.get(order_id=order_id)
            #获取对应的配送状态
            status = order.status
            full_address = f"{order.province}{order.city}{order.district}{order.address}"
            #根据配送状态来决定返回的route_map页面
            #获取订单中的物品信息
            order_items = order.items 
            user_request = {
                'latitude': order.latitude,
                'longitude': order.longitude,
                'items': order_items
            }
            # --- 2. 加载模型和环境 ---
            agent, env = load_model_and_environment()

            # --- 3. 构建状态 (重置环境) ---
            # env.reset 会使用传入的订单信息和内部的医院数据副本来构建初始状态
            # 并返回该状态向量
            state = env.reset(user_request, order_items)

            # --- 4. 智能体决策 (选择动作) ---
            # 确保 agent.epsilon = 0 以进行纯贪婪选择（不探索）
            agent.epsilon = 0.0 
            
            # 将状态转换为 PyTorch Tensor (如果需要)
            state_tensor = torch.FloatTensor(state).unsqueeze(0) # 添加 batch 维度
            # 使用 Q 网络计算 Q 值
            with torch.no_grad(): # 推理时关闭梯度计算
                q_values = agent.q_network(state_tensor)
            # 选择 Q 值最高的动作
            action = np.argmax(q_values.cpu().data.numpy())
            print(f"已选择动作: {action}")
            num_hospitals = len(env.hospitals_data) # 当前环境副本中的医院数
            
            # 执行动作并获取执行结果（包含选择理由）
            execution_result = env.action_space.execute_action(action, user_request, env.hospitals_data)
            
            if execution_result.get('action') == 'select_hospital':
                selected_hospital = execution_result.get('hospital')
                hospital_id = selected_hospital.get('id')
                hospital_name = selected_hospital.get('name', '未知医院')
                #根据医院名字拿到对应数据库中的信息
                hospital_info = Hospital.objects.filter(name=hospital_name).first()
                hospitals = Hospital.objects.all()
                hospitals_data = []
                for hospital in hospitals:
                    hospitals_data.append({
                        'name': hospital.name,
                        'longitude': hospital.longitude,
                        'latitude': hospital.latitude
                    })
                
                # 将 hospital_info 转换为可序列化的字典格式
                hospital_info_dict = {
                    'name': hospital_info.name,
                    'longitude': hospital_info.longitude,
                    'latitude': hospital_info.latitude
                } if hospital_info else None
                
                # 获取选择理由
                selection_reasons = execution_result.get('reasons', [])
                distance = execution_result.get('distance', 0)
                inventory_match = execution_result.get('inventory_match', 0)
                return render(request, 'route_map.html', {
                    'status': status,
                    'address': full_address,
                    'order_id': order_id,
                    'nearest_hospital': json.dumps(hospital_info_dict) if hospital_info_dict else json.dumps(None),
                    'hospitals': json.dumps(hospitals_data),
                    'selection_reasons': selection_reasons,  # 添加选择理由
                    'distance': distance,  # 添加距离信息
                    'inventory_match': inventory_match,  # 添加库存匹配度
                    'delivery_success': False,
                })
                
            elif execution_result.get('action') in ['wait_for_restock', 'redirect_alternative', 'split_order']:
                response_data = {
                    'status': 'success',
                    'action': execution_result.get('action'),
                    'message': execution_result.get('message', ''),
                    'reasons': execution_result.get('reasons', []),
                    'action_index': int(action)
                }
                return render(request, 'route_map.html', response_data)
            else:
                # 默认动作或错误
                response_data = {
                    'status': 'success',
                    'action': 'default',
                    'message': f'执行默认动作，索引 {action}',
                    'action_index': int(action)
                }

            return render(request,'route_map.html',response_data)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '请求数据格式错误'}, status=400)
        except FileNotFoundError as e:
            return JsonResponse({'status': 'error', 'message': f'模型或数据文件未找到: {str(e)}'}, status=500)
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # 打印详细错误信息到日志
            return JsonResponse({'status': 'error', 'message': f'处理请求时发生错误: {str(e)}'}, status=500)
        
@login_required
def check_order(request):
    """
    处理配送路径请求的视图。
    """
    if request.method == 'GET':
        try:
            print("用到了强化学习")
            # --- 1. 解析请求数据 ---
            order_id = request.GET.get('order_id')
            order = Order.objects.get(order_id=order_id)
            #获取对应的配送状态
            status = order.status
            full_address = f"{order.province}{order.city}{order.district}{order.address}"
            #根据配送状态来决定返回的route_map页面
            #获取订单中的物品信息
            order_items = order.items 
            user_request = {
                'latitude': order.latitude,
                'longitude': order.longitude,
                'items': order_items
            }
            # --- 2. 加载模型和环境 ---
            agent, env = load_model_and_environment()

            # --- 3. 构建状态 (重置环境) ---
            # env.reset 会使用传入的订单信息和内部的医院数据副本来构建初始状态
            # 并返回该状态向量
            state = env.reset(user_request, order_items)

            # --- 4. 智能体决策 (选择动作) ---
            # 确保 agent.epsilon = 0 以进行纯贪婪选择（不探索）
            agent.epsilon = 0.0 
            
            # 将状态转换为 PyTorch Tensor (如果需要)
            state_tensor = torch.FloatTensor(state).unsqueeze(0) # 添加 batch 维度
            # 使用 Q 网络计算 Q 值
            with torch.no_grad(): # 推理时关闭梯度计算
                q_values = agent.q_network(state_tensor)
            # 选择 Q 值最高的动作
            action = np.argmax(q_values.cpu().data.numpy())
            print(f"已选择动作: {action}")
            num_hospitals = len(env.hospitals_data) # 当前环境副本中的医院数
            
            # 执行动作并获取执行结果（包含选择理由）
            execution_result = env.action_space.execute_action(action, user_request, env.hospitals_data)
            
            if execution_result.get('action') == 'select_hospital':
                selected_hospital = execution_result.get('hospital')
                hospital_id = selected_hospital.get('id')
                hospital_name = selected_hospital.get('name', '未知医院')
                print('当前订单已配送至医院：', hospital_name)
                #根据医院名字拿到对应数据库中的信息
                hospital_info = Hospital.objects.filter(name=hospital_name).first()
                hospitals = Hospital.objects.all()
                hospitals_data = []
                for hospital in hospitals:
                    hospitals_data.append({
                        'name': hospital.name,
                        'longitude': hospital.longitude,
                        'latitude': hospital.latitude
                    })
                
                # 将 hospital_info 转换为可序列化的字典格式
                hospital_info_dict = {
                    'name': hospital_info.name,
                    'longitude': hospital_info.longitude,
                    'latitude': hospital_info.latitude
                } if hospital_info else None
                
                # 获取选择理由
                selection_reasons = execution_result.get('reasons', [])
                distance = execution_result.get('distance', 0)
                inventory_match = execution_result.get('inventory_match', 0)
                return render(request, 'route_map.html', {
                    'status': status,
                    'address': full_address,
                    'order_id': order_id,
                    'nearest_hospital': json.dumps(hospital_info_dict) if hospital_info_dict else json.dumps(None),
                    'hospitals': json.dumps(hospitals_data),
                    'selection_reasons': selection_reasons,  # 添加选择理由
                    'distance': distance,  # 添加距离信息
                    'inventory_match': inventory_match,  # 添加库存匹配度
                    'delivery_success': False,
                })
                
            elif execution_result.get('action') in ['wait_for_restock', 'redirect_alternative', 'split_order']:
                response_data = {
                    'status': 'success',
                    'action': execution_result.get('action'),
                    'message': execution_result.get('message', ''),
                    'reasons': execution_result.get('reasons', []),
                    'action_index': int(action)
                }
                return render(request, 'route_map.html', response_data)
            else:
                # 默认动作或错误
                response_data = {
                    'status': 'success',
                    'action': 'default',
                    'message': f'执行默认动作，索引 {action}',
                    'action_index': int(action)
                }

            return render(request,'route_map.html',response_data)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '请求数据格式错误'}, status=400)
        except FileNotFoundError as e:
            return JsonResponse({'status': 'error', 'message': f'模型或数据文件未找到: {str(e)}'}, status=500)
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # 打印详细错误信息到日志
            return JsonResponse({'status': 'error', 'message': f'处理请求时发生错误: {str(e)}'}, status=500)
        