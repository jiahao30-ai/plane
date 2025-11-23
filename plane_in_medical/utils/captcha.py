#生成验证码的内容
import random
import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import string


def random_str(length=4):
  """ 随机字符串 默认长度 4
   :param length: 默认长度 4
   :return:
   """
  return ''.join(random.sample(string.ascii_letters, length))

#生成验证码的颜色
def random_color():
  # RGB
  return random.randint(0,255),random.randint(0,255),random.randint(0,255)




# 生成验证码
def generate_captcha(width=160,height=40,length=4):
  # 创建一个空白图片
  image = Image.new('RGB',(width,height),color=(255,255,255))
  # 获取画布里的内容
  code = random_str()
  # 获取画笔
  draw = ImageDraw.Draw(image)
  # 随机颜色的填充
  for x in range(0,width,2):
    for y in range(height):
      draw.point((x,y),fill=random_color())
  # 获取字体
  font = ImageFont.truetype(os.path.join(os.path.dirname(__file__),'IMPACT.TTF'),size=30)
  # 将内容写入图片
  for t in range(length):
    # 通过画笔工具写入内容
    draw.text((40*t+5,5),code[t],font=font,fill=random_color())  
  # 图片的模糊
  #image = image.filter(ImageFilter.BLUR)
  # 返回图片，验证码
  return image,code

if __name__ == '__main__':
  # random_str()
  img ,code = generate_captcha()
  img.save('code.png')
  print(code)
