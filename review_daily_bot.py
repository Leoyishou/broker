import subprocess
import os
from datetime import datetime
from claude_agent import ClaudeAgent
from dotenv import load_dotenv
import logging

# 配置日志
log_file = 'review_daily_bot.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # 这会同时将日志输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def get_last_commit_diff(repo_path='.'):
    # 切换到仓库目录
    os.chdir(repo_path)

    try:
        # 获取最后一次提交的 hash
        last_commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()

        # 获取最后一次提交的 diff
        diff = subprocess.check_output(['git', 'show', last_commit_hash]).decode('utf-8')

        return diff

    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing git command: {e}")
        return None

def generate_daily_summary(repo_path, prompt_template):
    diff_text = get_last_commit_diff(repo_path)
    
    if not diff_text:
        logger.warning(f"Failed to get the diff of the last commit for {repo_path}.")
        return None

    # 从 .env 文件获取 API 密钥
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        logger.error("Please add 'CLAUDE_API_KEY' to your .env file")
        return None

    agent = ClaudeAgent(api_key)

    # 使用 format 方法将 diff_text 插入到 prompt_template 中
    prompt = prompt_template.format(diff_text=diff_text)

    logger.info(f"Sending prompt to Claude for daily summary generation for {repo_path}")
    response = agent.generate_response(prompt, max_tokens=1000)

    if response:
        logger.info(f"Successfully generated daily summary for {repo_path}")
        return response
    else:
        logger.warning(f"Failed to generate daily summary for {repo_path}")
        return None

def run_daily_summary(repo_path, repo_name):
    # 从 .env 文件获取提示模板
    prompt_template = os.getenv("PROMPT_TEMPLATE")

    if not prompt_template:
        logger.error("Please add 'PROMPT_TEMPLATE' to your .env file")
        return None

    summary = generate_daily_summary(repo_path, prompt_template)

    if summary:
        print(f"每日进度总结 ({repo_name})：")
        print(summary)

        # 创建保存总结的目录
        today = datetime.now().strftime("%Y-%m-%d")
        summary_dir = "每日回顾"
        os.makedirs(summary_dir, exist_ok=True)  # 如果目录不存在，创建它

        # 更改文件扩展名为 .md
        summary_file = os.path.join(summary_dir, f"daily_summary_{repo_name}_{today}.md")
        with open(summary_file, "w", encoding="utf-8") as f:
            # 添加 Markdown 格式的标题
            f.write(f"# {repo_name} 每日进度总结 - {today}\n\n")
            f.write(summary)
        logger.info(f"Daily summary for {repo_name} saved to {summary_file}")
        return summary
    else:
        logger.error(f"Failed to generate daily summary for {repo_name}")
        return None

def run_all_summaries():
    # 加载 .env 文件
    load_dotenv()

    # 从 .env 文件获取仓库路径
    brain_repo_path = os.getenv("BRAIN_REPO_PATH")
    qunar_repo_path = os.getenv("QUNAR_REPO_PATH")

    if not brain_repo_path or not qunar_repo_path:
        logger.error("Please add 'BRAIN_REPO_PATH' and 'QUNAR_REPO_PATH' to your .env file")
        return

    # 生成学习区总结
    brain_summary = run_daily_summary(brain_repo_path, "Brain")

    # 生成工作区总结
    qunar_summary = run_daily_summary(qunar_repo_path, "Qunar")

    return brain_summary, qunar_summary

if __name__ == "__main__":
    brain_summary, qunar_summary = run_all_summaries()
    
    if brain_summary:
        print("学习区总结已生成")
    else:
        print("学习区总结生成失败")

    if qunar_summary:
        print("工作区总结已生成")
    else:
        print("工作区总结生成失败")
