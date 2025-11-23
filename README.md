# 医飞速达 - 无人机医疗配送系统

<p align="center">
  <img src="static/images/logo1.png" alt="医飞速达Logo" width="200">
</p>

<p align="center">
  <a href="https://github.com/yourusername/plane_in_medical">
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python版本">
  </a>
  <a href="https://github.com/yourusername/plane_in_medical">
    <img src="https://img.shields.io/badge/Django-5.2.3-green" alt="Django版本">
  </a>
  <a href="https://github.com/yourusername/plane_in_medical">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="许可证">
  </a>
</p>

## 项目简介

医飞速达是一个基于Django框架的医疗无人机配送系统。项目结合了强化学习算法和Web开发技术，实现了智能路径规划和多医院协同库存管理。系统包含用户认证、商品浏览、购物车、订单管理、在线支付等完整电商功能，并通过强化学习优化配送路径，提高配送效率。前端采用响应式设计，后端使用MySQL数据库，支持多语言切换和用户个性化设置。

## 核心功能

### 🚀 智能配送系统
- 基于深度Q网络(DQN)的强化学习算法
- 多医院协同库存管理
- 智能路径优化与规划
- 实时配送状态追踪

### 🛒 完整电商功能
- 用户注册与登录系统
- 商品浏览与搜索
- 购物车管理
- 订单处理与支付
- 评论与反馈系统

### 🎨 用户体验
- 响应式前端设计
- 多语言支持(中英文)
- 直观的用户界面
- 实时聊天咨询

## 技术架构

### 后端技术栈
- **框架**: Django 5.2.3
- **数据库**: MySQL
- **缓存**: Redis
- **AI算法**: PyTorch + 强化学习(DQN)
- **地图服务**: 百度地图API

### 前端技术栈
- **模板引擎**: Django Templates
- **样式框架**: HTML5 + CSS3 + JavaScript
- **响应式设计**: 移动端适配
- **图标库**: Font Awesome

### 系统模块

plane_in_medical/   
├── login_app/ # 用户登录模块   
├── register_app/ # 用户注册模块   
├── shop_app/ # 商品管理模块   
├── pay_app/ # 支付模块   
├── order_app/ # 订单管理模块   
├── route_app/ # 路径规划模块   
├── communicate_app/ # 在线咨询模块   
├── search_app/ # 搜索模块   
├── user_app/ # 用户中心模块   
└── utils/ # 工具函数  
  
## 安装部署

### 环境要求
- Python 3.8+
- MySQL 5.7+
- Redis
- pip包管理器

### 安装步骤

1. **克隆项目**
```bash
git clone https://gitee.com/yourusername/plane_in_medical.git
cd plane_in_medical

2. 安装依赖

pip install -r requirements.txt

3. 配置数据库

CREATE DATABASE plane_in_medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

4. 初始化数据库

python manage.py makemigrations
python manage.py migrate
5. 启动服务

python manage.py runserver
