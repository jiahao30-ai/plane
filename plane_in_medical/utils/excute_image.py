import jieba.analyse
from openai import OpenAI
import base64
client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-641de691567b4ae8a3abf99362f6f5f7",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def encode_image_to_base64(image_file):
    """
    将图片文件对象转换为Base64编码
    """
    # 如果是Django的InMemoryUploadedFile对象
    if hasattr(image_file, 'read'):
        # 保存当前文件指针位置
        image_file.seek(0)
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    # 如果是文件路径字符串
    elif isinstance(image_file, str):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
        return encoded_string
    else:
        raise TypeError("image_file must be a file path string or file object")

def excute_medical_img(image_file, text=None):
    """
    处理医疗症状相关图片并返回结果,如果检测发现用户传的不是相关图片则回复你自己的职责
    :param image_file: Django InMemoryUploadedFile 对象或文件路径
    :param text: 用户输入的文本（可选）
    """
    try:
        # 将图片转换为Base64编码
        base64_image = encode_image_to_base64(image_file)
        
        # 构造医疗场景的提示模板
        medical_prompt = """您是一位专业的医疗智能助手，请根据用户上传的图片提供以下信息：

1. 症状识别：请识别图片中显示的症状（如皮疹、红肿、伤口等）
2. 初步分析：基于图片中的症状提供可能的原因分析
3. 建议措施：
   - 是否需要立即就医
   - 日常护理建议
   - 用药建议（如需要可推荐常见非处方药物）
   - 何时需要寻求专业医疗帮助

请注意：
- 您的分析仅供参考，不能替代专业医生的诊断
- 请提醒用户在症状严重或持续时及时就医
- 回答应简洁明了，使用通俗易懂的语言

用户附加的问题: {user_question}

请根据以上要求分析图片并提供专业建议。""".format(user_question=text if text else "请分析图片中的症状")
        
        completion = client.chat.completions.create(
            model="qwen-vl-plus",  # 模型名称
            messages=[{"role": "user","content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    {"type": "text", "text": medical_prompt},
                    ]}]
            )
        
        # 返回模型的回答
        return completion.model_dump_json()
        
    except Exception as e:
        print(f"处理医疗图片时出错: {e}")
        return str(e)
    
def extract_medicines(text):
    """
    从文本中提取药品名称并匹配数据库中的药品
    :param text: 输入的文本
    :return: 匹配的药品列表
    """
    #使用jieba分词库对其进行
    #文本内容进行截取，从要用药建议开始,何时需要寻求专业医疗帮助截止
    text = text[text.find('用药建议'):text.find('何时需要寻求专业医疗帮助')]
    keywords = jieba.analyse.extract_tags(text, topK=10,withWeight=False)
    print(keywords)
    return keywords



