# PO文件自动翻译工具

这是一个使用DeepSeek API自动翻译.po文件的Python工具。

## 功能特性

- 自动解析.po文件结构
- 提取需要翻译的msgid条目
- 批量调用DeepSeek API进行翻译
- 自动更新msgstr字段
- 支持配置文件管理
- 提供详细的翻译进度和统计

## 文件说明

- `po_translator.py` - 核心翻译器类和命令行工具
- `translate_po.py` - 简化的翻译脚本，使用配置文件
- `config_template.py` - 配置文件模板
- `requirements.txt` - Python依赖包列表

## 安装步骤

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 创建配置文件：
```bash
# 复制模板文件
copy config_template.py config.py
```

3. 编辑config.py文件，填入您的API信息：
```python
DEEPSEEK_API_KEY = "your_actual_api_key_here"  # 替换为您的真实API密钥
```

## 使用方法

### 方法一：使用简化脚本（推荐）

```bash
python translate_po.py
```

这种方法会：
- 自动读取config.py中的配置
- 显示翻译预览和确认
- 执行翻译并保存结果

### 方法二：使用命令行工具

```bash
python po_translator.py "Easy Game UI.po" --api-key YOUR_API_KEY
```

#### 命令行参数

- `po_file` - .po文件路径（必需）
- `--api-key` - DeepSeek API密钥（必需）
- `--api-url` - API地址（可选，默认使用官方地址）
- `--output` - 输出文件路径（可选，默认覆盖原文件）
- `--batch-size` - 每批翻译条目数（可选，默认10，仅在禁用智能批处理时使用）
- `--max-chars` - 每次API请求的最大字符数（可选，默认4000）
- `--language` - 目标语言（可选，默认"中文"）
- `--no-smart-batching` - 禁用智能批处理，使用固定批次大小（可选）
- `--dry-run` - 只解析不翻译（可选）

#### 示例

```bash
# 基本翻译（使用智能批处理）
python po_translator.py "Easy Game UI.po" --api-key sk-your-key

# 指定输出文件
python po_translator.py "Easy Game UI.po" --api-key sk-your-key -o "Easy Game UI_translated.po"

# 只测试解析，不翻译
python po_translator.py "Easy Game UI.po" --api-key sk-your-key --dry-run

# 使用固定批处理大小
python po_translator.py "Easy Game UI.po" --api-key sk-your-key --no-smart-batching --batch-size 5

# 自定义字符数限制
python po_translator.py "Easy Game UI.po" --api-key sk-your-key --max-chars 3000
```

## 配置说明

在`config.py`中可以设置以下参数：

```python
# API配置
DEEPSEEK_API_KEY = "your_api_key_here"  # DeepSeek API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"  # API地址

# 翻译配置
TARGET_LANGUAGE = "中文"  # 目标语言
BATCH_SIZE = 10  # 每批翻译条目数（仅在禁用智能批处理时使用）

# 智能批处理配置
USE_SMART_BATCHING = True  # 是否启用智能批处理（基于内容长度）
MAX_CHARS_PER_REQUEST = 4000  # 每次API请求的最大字符数

# 文件路径
PO_FILE_PATH = r"c:\path\to\your\file.po"  # .po文件完整路径
OUTPUT_FILE_PATH = None  # 输出路径，None表示覆盖原文件
```

### 智能批处理功能

新增的智能批处理功能可以根据内容长度动态调整批次大小，避免单次API调用内容过长导致的失败：

- **自动长度检测**：估算每个批次的总字符数
- **动态分批**：当内容超过限制时自动缩小批次
- **重试机制**：失败时自动重试，避免临时网络问题
- **进度显示**：显示详细的批次信息和翻译进度

## 工作原理

1. **解析阶段**：
   - 读取.po文件
   - 解析每个翻译条目的Key、msgid、msgstr等信息
   - 过滤出需要翻译的条目（msgid不为空且msgstr为空）

2. **翻译阶段**：
   - 将多个msgid用管道符"|"连接成批次
   - 构建翻译提示发送给DeepSeek API
   - 解析返回的翻译结果

3. **更新阶段**：
   - 将翻译结果写入对应的msgstr字段
   - 保存更新后的.po文件

## 注意事项

1. **API密钥安全**：请妥善保管您的DeepSeek API密钥，不要提交到版本控制系统

2. **网络连接**：需要稳定的网络连接访问DeepSeek API

3. **文件备份**：建议在翻译前备份原始.po文件

4. **批处理大小**：建议batch_size设置为5-20之间，太大可能导致API超时，太小效率较低

5. **成本控制**：API调用是收费的，请根据需要控制翻译的条目数量

## 故障排除

### 常见问题

1. **导入配置失败**：
   - 确保config.py文件存在且语法正确
   - 检查文件路径是否正确

2. **API调用失败**：
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证API账户余额

3. **文件解析错误**：
   - 确认.po文件格式正确
   - 检查文件编码是否为UTF-8

4. **翻译结果不准确**：
   - 可以调整翻译提示词
   - 减小batch_size以提高翻译质量

### 调试模式

使用`--dry-run`参数可以只解析文件而不进行翻译，用于测试解析是否正常：

```bash
python po_translator.py "Easy Game UI.po" --api-key sk-your-key --dry-run
```

## 示例输出

```
=== PO文件自动翻译工具 ===
文件路径: c:\Users\ZzxxH\Documents\Unreal Projects\SH\Easy Game UI.po
目标语言: 中文
批处理大小: 10
输出路径: 覆盖原文件

正在解析文件: c:\Users\ZzxxH\Documents\Unreal Projects\SH\Easy Game UI.po
解析完成，找到 186 个待翻译条目

前几个待翻译条目示例:
1. Default
2. Default
3. Placeholder Text
4. Settings
5. Back
... 还有 181 个条目

将翻译 186 个条目，预计需要 19 次API调用
确认继续？(y/N): y

开始翻译 186 个条目...
正在翻译第 1 批（10 个条目）...
第 1 批翻译完成
正在翻译第 2 批（10 个条目）...
第 2 批翻译完成
...

翻译结果已保存到: c:\Users\ZzxxH\Documents\Unreal Projects\SH\Easy Game UI.po

翻译摘要:
总条目数: 186
已翻译: 184
未翻译: 2
翻译率: 98.9%

翻译完成！
```