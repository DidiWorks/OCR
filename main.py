import os
# 禁用PaddlePaddle的OneDNN优化，避免兼容性问题
os.environ['FLAGS_use_mkldnn'] = 'False'
os.environ['FLAGS_use_cudnn'] = 'False'
os.environ['FLAGS_use_gpu'] = 'False'

from app import run_app

if __name__ == "__main__":
    run_app()