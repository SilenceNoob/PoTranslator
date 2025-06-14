# Debug功能使用指南

## 概述
新增了Debug功能，可以详细输出翻译过程中的API交互信息，帮助用户了解翻译过程和调试问题。

## 启用Debug模式

### 方法一：通过配置文件（推荐）
在 `config.py` 中设置：
```python
DEBUG = True  # 启用调试模式
```

然后运行：
```bash
python translate_po.py
```

### 方法二：通过命令行参数
```bash
python po_translator.py "your_file.po" --api-key "your_api_key" --debug
```

## Debug输出内容

当启用debug模式时，程序会输出：

### 1. 发送给AI的完整内容
```
==================================================
🔍 [DEBUG] 发送给AI的完整内容:
--------------------------------------------------
模型: deepseek-chat
温度: 0.3
最大token数: 2000
请求内容:
请将以下文本翻译成中文。文本之间用"|"分隔，请保持相同的分隔符格式返回翻译结果。

原文：
Hello World|Click to continue|Exit game

翻译要求：
1. 保持原有的格式和标点符号
2. 如果是游戏界面相关的术语，请使用常见的游戏本地化翻译
3. 保持专业和准确的翻译
4. 用"|"分隔每个翻译结果
5. 除了翻译结果外，不要输出任何其他多余文本内容
==================================================
```

### 2. AI回应的完整内容
```
==================================================
🤖 [DEBUG] AI回应的完整内容:
--------------------------------------------------
原始回应:
你好世界|点击继续|退出游戏
--------------------------------------------------
Token使用情况:
  输入token: 150
  输出token: 25
  总token: 175
==================================================
```

### 3. 解析后的翻译结果
```
📝 [DEBUG] 解析后的翻译结果:
--------------------------------------------------
1. 原文: Hello World
   译文: 你好世界

2. 原文: Click to continue
   译文: 点击继续

3. 原文: Exit game
   译文: 退出游戏

==================================================
```

## 使用场景

Debug模式特别适用于：

1. **排查翻译质量问题**：查看AI的原始回应，了解是否是解析问题
2. **监控API使用情况**：查看token消耗，优化批次大小
3. **开发和测试**：验证请求内容是否正确
4. **故障排除**：当翻译结果异常时，查看完整的交互过程

## 注意事项

- Debug模式会产生大量输出，建议只在需要时启用
- 输出内容包含完整的API交互，可能包含敏感信息
- 在生产环境中建议关闭Debug模式以提高性能

## 配置文件中的Debug选项

```python
# 调试配置
DEBUG = False  # 是否启用调试模式，输出详细的API交互信息
```

设置为 `True` 启用，`False` 禁用。
