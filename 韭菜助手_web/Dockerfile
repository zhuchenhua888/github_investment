# 使用官方 Python 轻量级镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 80

# 安装系统依赖（如果需要的话，例如 pandas/numpy 可能需要一些 C 库）
# 对于基础的 pandas/numpy，slim 镜像通常足够，如果报错可以取消下面的注释
# RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# 使用国内镜像加速（可选，微信云托管构建环境通常在海外或有自己的加速）
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（微信云托管默认监听 80）
EXPOSE 80

# 启动命令
# 建议在生产环境使用 gunicorn 代替 flask 自带服务器
# RUN pip install gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

# 目前先使用 flask 自带服务器启动（方便调试，部署到云托管建议后续改为 gunicorn）
CMD ["python", "app.py"]
