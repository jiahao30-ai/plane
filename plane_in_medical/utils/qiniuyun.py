# -*- coding: utf-8 -*-
# flake8: noqa
from qiniu import Auth, put_data, BucketManager
import os

def upload_file(ak, sk, localfile, key=None):
    #构建鉴权对象
    q = Auth(ak, sk)
    #要上传的空间
    bucket_name = 'yifeisuda1'

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    ret, info = put_data(token, key, localfile)
    if ret:
        print("上传成功")
    return ret.get('key') if ret else None

def upload_medicine_images():
    """
    将media/medicine_images文件夹中的所有图片上传到七牛云存储的medicine文件夹中
    """
    # 设置访问凭证
    access_key = 'fpc5KAJBEd0kNn0ega-YK54KWkjl0q8k3A7r6Pjr'
    secret_key = 'Tkv0FY8gv6kQqvtdaPeTPOKKXbOytWR4FFYzEahP'
    
    # 本地图片文件夹路径
    local_image_dir = 'media'

    # 初始化Auth和BucketManager
    q = Auth(access_key, secret_key)
    bucket = BucketManager(q)
    
    # 获取bucket中已有的文件列表，避免重复上传
    bucket_name = 'yifeisuda1'
    existing_files = set()
    marker = None
    
    # 获取所有已存在的文件名
    while True:
        ret, eof, info = bucket.list(bucket_name, prefix='medicine/', marker=marker)
        if ret and 'items' in ret:
            for item in ret['items']:
                existing_files.add(item['key'])
        if eof:
            break
        marker = ret.get('marker') if ret else None
    
    # 遍历本地图片文件夹
    uploaded_count = 0
    skipped_count = 0
    
    for filename in os.listdir(local_image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # 构造在七牛云存储中的文件名（medicine/文件夹下）
            remote_filename = f'medicine/{filename}'
            
            # 检查文件是否已存在
            if remote_filename in existing_files:
                print(f"文件 {filename} 已存在，跳过上传")
                skipped_count += 1
                continue
            
            # 读取本地文件并上传
            local_file_path = os.path.join(local_image_dir, filename)
            with open(local_file_path, 'rb') as f:
                file_data = f.read()
                result = upload_file(access_key, secret_key, file_data, remote_filename)
                if result:
                    print(f"成功上传: {filename} -> {result}")
                    uploaded_count += 1
                else:
                    print(f"上传失败: {filename}")
    
    print(f"上传完成！成功上传 {uploaded_count} 个文件，跳过 {skipped_count} 个已存在文件")

if __name__ == '__main__':
    upload_medicine_images()