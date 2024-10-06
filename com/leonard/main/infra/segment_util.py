import jieba
import re
from opencc import OpenCC

def segment_and_deduplicate(text):
    # 初始化繁体到简体的转换器
    cc = OpenCC('t2s')
    
    # 预处理文本,移除时间戳和特殊字符，并转换为简体
    lines = text.split('\n')
    cleaned_lines = [cc.convert(re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:', '', line).strip()) for line in lines if line.strip()]
    cleaned_text = ' '.join(cleaned_lines)
    
    # 分词
    words = jieba.lcut(cleaned_text)
    
    # 去重并排序
    unique_words = sorted(set(words))
    
    return unique_words

