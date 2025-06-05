#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的PO文件翻译脚本
使用配置文件中的设置自动翻译.po文件
"""

import os
import sys
from po_translator import POTranslator

def main():
    # 尝试导入配置
    try:
        import config
        api_key = config.DEEPSEEK_API_KEY
        api_url = getattr(config, 'DEEPSEEK_API_URL', None)
        target_language = getattr(config, 'TARGET_LANGUAGE', '中文')
        batch_size = getattr(config, 'BATCH_SIZE', 10)
        max_chars_per_request = getattr(config, 'MAX_CHARS_PER_REQUEST', 4000)
        use_smart_batching = getattr(config, 'USE_SMART_BATCHING', True)
        debug = getattr(config, 'DEBUG', False)
        po_file = config.PO_FILE_PATH
        output_file = getattr(config, 'OUTPUT_FILE_PATH', None)
    except ImportError:
        print("错误：未找到config.py文件")
        print("请复制config_template.py为config.py并填入您的API信息")
        return False
    except AttributeError as e:
        print(f"错误：配置文件缺少必要的配置项: {e}")
        return False
    
    # 验证配置
    if not api_key or api_key == "your_api_key_here":
        print("错误：请在config.py中设置有效的DEEPSEEK_API_KEY")
        return False
    
    if not os.path.exists(po_file):
        print(f"错误：.po文件不存在: {po_file}")
        return False
    
    print("=== PO文件自动翻译工具 ===")
    print(f"文件路径: {po_file}")
    print(f"目标语言: {target_language}")
    print(f"智能批处理: {'启用' if use_smart_batching else '禁用'}")
    print(f"调试模式: {'启用' if debug else '禁用'}")
    if use_smart_batching:
        print(f"最大字符数/请求: {max_chars_per_request}")
    else:
        print(f"固定批处理大小: {batch_size}")
    print(f"输出路径: {output_file or '覆盖原文件'}")
    print()
    
    # 询问用户确认
    confirm = input("是否开始翻译？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print("翻译已取消")
        return False
      # 初始化翻译器
    translator = POTranslator(api_key, api_url, max_chars_per_request, debug)
    
    try:
        # 解析PO文件
        print(f"正在解析文件: {po_file}")
        entries = translator.parse_po_file(po_file)
        print(f"解析完成，找到 {len(entries)} 个待翻译条目")
        
        if len(entries) == 0:
            print("没有找到需要翻译的条目")
            return True
        
        # 显示一些示例条目
        print("\n前几个待翻译条目示例:")
        for i, entry in enumerate(entries[:5]):
            print(f"{i+1}. {entry.msgid}")
        if len(entries) > 5:
            print(f"... 还有 {len(entries) - 5} 个条目")
          # 最终确认
        batching_info = "智能批处理（基于内容长度）" if use_smart_batching else f"固定批处理（每批{batch_size}个）"
        print(f"\n将翻译 {len(entries)} 个条目，使用{batching_info}")
        final_confirm = input("确认继续？(y/N): ").strip().lower()
        if final_confirm not in ['y', 'yes', '是']:
            print("翻译已取消")
            return False
        
        # 执行翻译
        translator.translate_entries(batch_size, target_language, use_smart_batching)
        
        # 写入结果
        translator.write_po_file(po_file, output_file)
        
        # 打印摘要
        translator.print_summary()
        
        print("\n翻译完成！")
        return True
        
    except Exception as e:
        print(f"翻译过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
