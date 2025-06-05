# PO翻译器配置文件
# 复制此文件为 config.py 并填入您的API信息

# DeepSeek API配置
DEEPSEEK_API_KEY = "your_api_key_here"  # 请替换为您的DeepSeek API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"  # API地址

# 翻译配置
TARGET_LANGUAGE = "中文"  # 目标语言
BATCH_SIZE = 10  # 每批翻译的条目数量（仅在禁用智能批处理时使用）

# 智能批处理配置
USE_SMART_BATCHING = True  # 是否启用智能批处理（基于内容长度）
MAX_CHARS_PER_REQUEST = 4000  # 每次API请求的最大字符数

# 调试配置
DEBUG = False  # 是否启用调试模式，输出详细的API交互信息

# 文件路径
PO_FILE_PATH = r"c:\Users\ZzxxH\Documents\Unreal Projects\SH\Easy Game UI.po"  # .po文件路径
OUTPUT_FILE_PATH = None  # 输出文件路径，None表示覆盖原文件
