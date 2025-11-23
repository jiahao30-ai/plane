from django.shortcuts import render
from login_app.models import User as user
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from shop_app.models import Medicine
from http import HTTPStatus
from dashscope import Application
from utils.excute_image import excute_medical_img, extract_medicines as extract_medicine_keywords

@login_required
def chat_view(request):
    method = request.method
    # 获取用户头像
    try:
        user_avatar = user.objects.get(username=request.user).avatar
    except:
        user_avatar = None
        
    if method == 'GET':
        return render(request,'chat.html',{
            'answer':None,
            'user_avatar': user_avatar
        })
    else:  # POST 请求
        # 接受用户传递过来的参数
        question = request.POST.get('question')

        response = Application.call(
            # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
            api_key="sk-641de691567b4ae8a3abf99362f6f5f7",
            app_id="7a4eaca8970a48c28d90758627928b4b",
            prompt=question)

        if response.status_code != HTTPStatus.OK:
            print(f'request_id={response.request_id}')
            print(f'code={response.status_code}')
            print(f'message={response.message}')
            print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
            answer = "抱歉，处理您的请求时出现错误，请稍后再试。"
        else:
            answer = response.output.text
            
        # 获取关键词
        keywords = extract_medicine_keywords(answer)
        # 找出与关键词匹配的药品
        medicines = Medicine.objects.filter(name__in=keywords)
        
        # 如果是 AJAX 请求，返回 JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'answer': answer, 
                'status': 'success',
                'medicines': [medicine.name for medicine in medicines],
                'images': [medicine.full_image_url() for medicine in medicines],
            })
        else:
            # 非 AJAX 请求，返回完整页面
            return render(request,'chat.html',{
                'answer':answer,
                'user_avatar': user_avatar
            })

@login_required
def execute_image_text(request):
    if request.method == 'POST':
        # 获取用户上传的图片
        image_file = request.FILES.get('image')
        # 获取用户输入的文本
        text = request.POST.get('text')
        
        if not image_file:
            return JsonResponse({
                'status': 'error',
                'message': '未提供图片文件'
            }, status=400)
        
        try:
            result_json = excute_medical_img(image_file, text)
            
            # 解析返回的JSON结果
            result = json.loads(result_json)
            
            # 提取模型的回答文本
            answer_text = result['choices'][0]['message']['content']
            # 获取关键词
            keywords = extract_medicine_keywords(answer_text)
            
            # 获取所有药品名称
            all_medicines = Medicine.objects.all()
            medicines = []
            
            # 找出与关键词匹配的药品，筛选出keywords在medicines中的药品
            for keyword in keywords:
                for medicine in all_medicines:
                    # 精确匹配
                    if keyword == medicine.name:
                        if medicine not in medicines:
                            medicines.append(medicine)
                    # 部分匹配（关键词在药品名中）
                    elif keyword in medicine.name and len(keyword) >= 2:
                        if medicine not in medicines:
                            medicines.append(medicine)
            
            
            return JsonResponse({
                'status': 'success',
                'answer': answer_text,
                'medicines': [medicine.name for medicine in medicines],
                'images': [medicine.full_image_url for medicine in medicines],
            })
        except Exception as e:
            print(f"处理图片时出错: {e}")
            import traceback
            traceback.print_exc()  # 打印详细的错误堆栈信息
            return JsonResponse({
                'status': 'error',
                'message': f'处理图片时出错: {str(e)}'
            }, status=500)