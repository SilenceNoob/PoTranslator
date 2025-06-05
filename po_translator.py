#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO文件自动翻译脚本
使用DeepSeek API自动翻译.po文件中的msgid到msgstr
"""

import re
import requests
import json
import argparse
import os
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class POEntry:
    """PO文件条目结构"""
    key: str
    source_location: str
    msgctxt: str
    msgid: str
    msgstr: str
    line_start: int
    line_end: int


class POTranslator:
    def __init__(self, api_key: str = None, api_url: str = None, max_chars_per_request: int = 4000):
        """
        初始化翻译器
        
        Args:
            api_key: DeepSeek API密钥
            api_url: DeepSeek API URL，默认为官方API
            max_chars_per_request: 每次API请求的最大字符数
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.deepseek.com/chat/completions"
        self.max_chars_per_request = max_chars_per_request
        self.entries: List[POEntry] = []
        
    def parse_po_file(self, file_path: str) -> List[POEntry]:
        """
        解析.po文件，提取所有条目
        
        Args:
            file_path: .po文件路径
            
        Returns:
            提取的PO条目列表
        """
        entries = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找Key注释行
            if line.startswith('#. Key:'):
                entry = self._parse_entry(lines, i)
                if entry and entry.msgid and entry.msgid != '""' and entry.msgid.strip() != "":
                    entries.append(entry)
                    i = entry.line_end
                else:
                    i += 1
            else:
                i += 1
        
        self.entries = entries
        return entries
    
    def _parse_entry(self, lines: List[str], start_idx: int) -> Optional[POEntry]:
        """
        解析单个PO条目
        
        Args:
            lines: 文件所有行
            start_idx: 开始解析的行索引
            
        Returns:
            解析出的PO条目或None
        """
        try:
            i = start_idx
            entry = POEntry("", "", "", "", "", start_idx, start_idx)
            
            # 解析Key
            key_line = lines[i].strip()
            if key_line.startswith('#. Key:'):
                entry.key = key_line.split('Key:', 1)[1].strip()
                i += 1
            
            # 解析SourceLocation
            if i < len(lines) and lines[i].strip().startswith('#. SourceLocation:'):
                entry.source_location = lines[i].strip().split('SourceLocation:', 1)[1].strip()
                i += 1
            
            # 跳过其他注释行（如#:行）
            while i < len(lines) and lines[i].strip().startswith('#'):
                i += 1
            
            # 解析msgctxt
            if i < len(lines) and lines[i].strip().startswith('msgctxt'):
                entry.msgctxt = self._extract_quoted_string(lines[i])
                i += 1
            
            # 解析msgid
            if i < len(lines) and lines[i].strip().startswith('msgid'):
                entry.msgid = self._extract_quoted_string(lines[i])
                i += 1
                
                # 处理多行msgid
                while i < len(lines) and lines[i].strip().startswith('"'):
                    additional = self._extract_quoted_string(lines[i])
                    if additional:
                        entry.msgid += additional
                    i += 1
            
            # 解析msgstr
            if i < len(lines) and lines[i].strip().startswith('msgstr'):
                entry.msgstr = self._extract_quoted_string(lines[i])
                i += 1
                
                # 处理多行msgstr
                while i < len(lines) and lines[i].strip().startswith('"'):
                    additional = self._extract_quoted_string(lines[i])
                    if additional:
                        entry.msgstr += additional
                    i += 1
            
            entry.line_end = i
            return entry
            
        except Exception as e:
            print(f"解析条目时出错（行 {start_idx}）: {e}")
            return None
    
    def _extract_quoted_string(self, line: str) -> str:
        """
        从行中提取引号内的字符串
        
        Args:
            line: 包含引号字符串的行
            
        Returns:
            提取的字符串内容
        """
        match = re.search(r'"([^"]*)"', line)
        return match.group(1) if match else ""
    
    def _estimate_token_count(self, text: str) -> int:
        """
        估算文本的token数量（简单估算，1个token约等于4个字符）
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        return len(text) // 4 + 1
    
    def _estimate_batch_content_length(self, msgids: List[str], prompt_template: str) -> int:
        """
        估算批次内容的总长度
        
        Args:
            msgids: 待翻译的文本列表
            prompt_template: 提示模板
            
        Returns:
            估算的总字符数
        """
        combined_text = "|".join(msgids)
        full_prompt = prompt_template.replace("{combined_text}", combined_text)
        return len(full_prompt)
    
    def _create_smart_batches(self, msgids: List[str], target_language: str = "中文") -> List[List[str]]:
        """
        智能创建批次，考虑内容长度限制
        
        Args:
            msgids: 待翻译的文本列表
            target_language: 目标语言
            
        Returns:
            智能分组后的批次列表
        """
        prompt_template = f"""请将以下文本翻译成{target_language}。文本之间用"|"分隔，请保持相同的分隔符格式返回翻译结果。

原文：
{{combined_text}}

翻译要求：
1. 保持原有的格式和标点符号
2. 如果是游戏界面相关的术语，请使用常见的游戏本地化翻译
3. 保持专业和准确的翻译
4. 用"|"分隔每个翻译结果
5. 除了翻译结果外，不要输出任何其他多余文本内容
"""
        
        batches = []
        current_batch = []
        
        for msgid in msgids:
            # 检查添加当前项目后是否超出限制
            test_batch = current_batch + [msgid]
            estimated_length = self._estimate_batch_content_length(test_batch, prompt_template)
            
            if estimated_length > self.max_chars_per_request and current_batch:
                # 如果超出限制且当前批次不为空，保存当前批次并开始新批次
                batches.append(current_batch)
                current_batch = [msgid]
            else:
                # 如果未超出限制，添加到当前批次
                current_batch.append(msgid)
                
            # 检查单个项目是否过长
            single_item_length = self._estimate_batch_content_length([msgid], prompt_template)
            if single_item_length > self.max_chars_per_request:
                print(f"警告：单个条目过长（{single_item_length} 字符），可能需要拆分: {msgid[:100]}...")
          # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def translate_batch(self, msgids: List[str], target_language: str = "中文", retry_count: int = 3) -> List[str]:
        """
        批量翻译文本（带重试机制）
        
        Args:
            msgids: 待翻译的文本列表
            target_language: 目标语言
            retry_count: 重试次数
            
        Returns:
            翻译结果列表
        """
        if not self.api_key:
            raise ValueError("API密钥未设置")
        
        # 检查批次大小
        combined_text = "|".join(msgids)
        if len(combined_text) > self.max_chars_per_request:
            print(f"警告：批次内容过长（{len(combined_text)} 字符），可能导致API调用失败")
        
        # 构建翻译提示
        prompt = f"""请将以下文本翻译成{target_language}。文本之间用"|"分隔，请保持相同的分隔符格式返回翻译结果。

原文：
{combined_text}

翻译要求：
1. 保持原有的格式和标点符号
2. 如果是游戏界面相关的术语，请使用常见的游戏本地化翻译
3. 保持专业和准确的翻译
4. 用"|"分隔每个翻译结果
5. 除了翻译结果外，不要输出任何其他多余文本内容
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 动态调整max_tokens基于输入长度
        estimated_output_tokens = self._estimate_token_count(combined_text) * 2  # 翻译通常比原文长
        max_tokens = min(max(estimated_output_tokens, 1000), 4000)  # 限制在1000-4000之间
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens
        }

        for attempt in range(retry_count):
            try:
                print(f"  发送API请求（尝试 {attempt + 1}/{retry_count}）...")
                response = requests.post(self.api_url, headers=headers, json=data, timeout=120)
                response.raise_for_status()
                
                result = response.json()
                translated_text = result["choices"][0]["message"]["content"].strip()
                
                # 解析翻译结果
                translations = self._parse_translation_result(translated_text, len(msgids))
                
                print(f"  API调用成功，返回 {len(translations)} 个翻译结果")
                return translations
                
            except requests.exceptions.Timeout:
                print(f"  API请求超时（尝试 {attempt + 1}/{retry_count}）")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
            except requests.exceptions.RequestException as e:
                print(f"  API请求失败（尝试 {attempt + 1}/{retry_count}）: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
            except (KeyError, IndexError) as e:
                print(f"  解析API响应失败（尝试 {attempt + 1}/{retry_count}）: {e}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
        
        print(f"  所有重试都失败，返回空翻译结果")
        return [""] * len(msgids)
    
    def _parse_translation_result(self, translated_text: str, expected_count: int) -> List[str]:
        """
        解析翻译结果
        
        Args:
            translated_text: API返回的翻译文本
            expected_count: 期望的翻译数量
            
        Returns:
            解析后的翻译列表
        """
        # 移除可能的前缀文本（如"翻译结果："）
        lines = translated_text.split('\n')
        for i, line in enumerate(lines):
            if '|' in line and not line.startswith(('翻译结果', '译文', '结果')):
                translated_text = '\n'.join(lines[i:])
                break
        
        # 解析翻译结果
        translations = translated_text.split("|")
        
        # 清理每个翻译结果
        translations = [t.strip() for t in translations]
        
        # 确保返回的翻译数量与输入相同
        if len(translations) != expected_count:
            print(f"    警告：翻译结果数量不匹配。期望：{expected_count}，实际：{len(translations)}")
            
            # 如果翻译结果过多，截断
            if len(translations) > expected_count:
                translations = translations[:expected_count]
            
            # 如果翻译结果不足，补齐        while len(translations) < expected_count:
                translations.append("")
        
        return translations
    
    def translate_entries(self, batch_size: int = 10, target_language: str = "中文", use_smart_batching: bool = True):
        """
        翻译所有条目
        
        Args:
            batch_size: 每批翻译的条目数量（仅在不使用智能批处理时有效）
            target_language: 目标语言
            use_smart_batching: 是否使用智能批处理（考虑内容长度）
        """
        if not self.entries:
            print("没有找到需要翻译的条目")
            return
        
        print(f"开始翻译 {len(self.entries)} 个条目...")
        
        # 提取所有msgid
        msgids = [entry.msgid for entry in self.entries]
        
        if use_smart_batching:
            # 使用智能批处理
            batches = self._create_smart_batches(msgids, target_language)
            print(f"智能批处理：创建了 {len(batches)} 个批次")
            
            # 打印批次信息
            for i, batch in enumerate(batches):
                combined_length = len("|".join(batch))
                print(f"  批次 {i+1}: {len(batch)} 个条目，总长度 {combined_length} 字符")
        else:
            # 使用固定大小批处理
            batches = []
            for i in range(0, len(msgids), batch_size):
                batches.append(msgids[i:i + batch_size])
            print(f"固定批处理：创建了 {len(batches)} 个批次，每批最多 {batch_size} 个条目")
        
        # 翻译每个批次
        total_translated = 0
        for i, batch_msgids in enumerate(batches):
            print(f"\n正在翻译第 {i + 1}/{len(batches)} 批（{len(batch_msgids)} 个条目）...")
            
            try:
                translations = self.translate_batch(batch_msgids, target_language)
                
                # 更新翻译结果
                start_idx = sum(len(batches[j]) for j in range(i))
                for j, translation in enumerate(translations):
                    entry_idx = start_idx + j
                    if entry_idx < len(self.entries) and translation.strip():
                        self.entries[entry_idx].msgstr = translation
                        total_translated += 1
                        
                print(f"第 {i + 1} 批翻译完成，成功翻译 {sum(1 for t in translations if t.strip())} 个条目")
                
                # 添加延迟避免API限制
                if i < len(batches) - 1:  # 不是最后一批
                    time.sleep(1)
                
            except Exception as e:
                print(f"第 {i + 1} 批翻译失败: {e}")
                continue
        
        print(f"\n翻译完成！总共翻译了 {total_translated} 个条目")
    
    def write_po_file(self, input_file: str, output_file: str = None):
        """
        将翻译结果写回.po文件
        
        Args:
            input_file: 原始.po文件路径
            output_file: 输出文件路径，默认覆盖原文件
        """
        if output_file is None:
            output_file = input_file
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 创建条目字典以便快速查找
        entry_dict = {entry.key: entry for entry in self.entries}
        
        # 修改文件内容
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找Key注释行
            if line.startswith('#. Key:'):
                key = line.split('Key:', 1)[1].strip()
                
                if key in entry_dict:
                    entry = entry_dict[key]
                    
                    # 查找msgstr行并替换
                    j = i
                    while j < len(lines) and j <= entry.line_end:
                        if lines[j].strip().startswith('msgstr'):
                            # 替换msgstr行
                            if entry.msgstr:
                                lines[j] = f'msgstr "{entry.msgstr}"\n'
                            break
                        j += 1
                    
                    i = entry.line_end
                else:
                    i += 1
            else:
                i += 1
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"翻译结果已保存到: {output_file}")
    
    def print_summary(self):
        """打印翻译摘要"""
        total = len(self.entries)
        translated = sum(1 for entry in self.entries if entry.msgstr and entry.msgstr.strip())
        
        print(f"\n翻译摘要:")
        print(f"总条目数: {total}")
        print(f"已翻译: {translated}")
        print(f"未翻译: {total - translated}")
        print(f"翻译率: {translated/total*100:.1f}%" if total > 0 else "翻译率: 0%")


def main():
    parser = argparse.ArgumentParser(description="PO文件自动翻译工具")
    parser.add_argument("po_file", help=".po文件路径")
    parser.add_argument("--api-key", required=True, help="DeepSeek API密钥")
    parser.add_argument("--api-url", help="API URL（可选）")
    parser.add_argument("--output", "-o", help="输出文件路径（默认覆盖原文件）")
    parser.add_argument("--batch-size", type=int, default=10, help="每批翻译的条目数量（仅在禁用智能批处理时使用）")
    parser.add_argument("--max-chars", type=int, default=4000, help="每次API请求的最大字符数")
    parser.add_argument("--language", default="中文", help="目标语言")
    parser.add_argument("--no-smart-batching", action="store_true", help="禁用智能批处理，使用固定批次大小")
    parser.add_argument("--dry-run", action="store_true", help="只解析文件，不进行翻译")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.po_file):
        print(f"错误：文件不存在 {args.po_file}")
        return
    
    # 初始化翻译器
    translator = POTranslator(args.api_key, args.api_url, args.max_chars)
    
    # 解析PO文件
    print(f"正在解析文件: {args.po_file}")
    entries = translator.parse_po_file(args.po_file)
    print(f"解析完成，找到 {len(entries)} 个待翻译条目")
    
    if args.dry_run:
        translator.print_summary()
        return
    
    # 执行翻译
    use_smart_batching = not args.no_smart_batching
    translator.translate_entries(args.batch_size, args.language, use_smart_batching)
    
    # 写入结果
    output_file = args.output or args.po_file
    translator.write_po_file(args.po_file, output_file)
    
    # 打印摘要
    translator.print_summary()


if __name__ == "__main__":
    main()
