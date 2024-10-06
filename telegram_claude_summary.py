from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
from datetime import date, datetime, timedelta
import pytz  # 添加这行
from claude_agent import ClaudeAgent
from dotenv import load_dotenv
import os
import json
# Create the chat_logs directory if it doesn't exist
os.makedirs("chat_logs", exist_ok=True)

# 定义东八区时区
beijing_tz = pytz.timezone('Asia/Shanghai')

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def summarize_with_claude(chat_log_file):
    load_dotenv()
    api_key = os.getenv("CLAUDE_API_KEY")
    prompt_template = os.getenv("SUMMARY_PROMPT_TEMPLATE")

    if not api_key or not prompt_template:
        print("请在 .env 文件中添加 CLAUDE_API_KEY 和 SUMMARY_PROMPT_TEMPLATE")
        return

    with open(chat_log_file, 'r', encoding='utf-8') as f:
        chat_content = f.read()

    prompt = prompt_template.format(chat_content=chat_content)

    agent = ClaudeAgent(api_key)
    summary = agent.generate_response(prompt, max_tokens=2000)

    if summary:
        summary_file = "telegram_summaries.md"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## Summary for {current_time}\n\n")
            f.write(summary)
        print(f"总结已追加到 {summary_file}")
    else:
        print("生成总结失败")

# 请填写您的api_id, api_hash和phone
api_id = '26421064'
api_hash = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
phone = '+12068619306'
# 目标群组的username或id
channel_username = '勃勃的美股投资日报会员群'
subgroup_name = '中概之家'

client = TelegramClient('session', api_id, api_hash)

async def main(hours_ago=1):  # 添加 hours_ago 参数，默认为 1 小时
    # 拿到 clinet
    await client.start()
    print("Client Created")

    # 获取所有对话
    dialogs = await client.get_dialogs()

    # 找到目标频道
    target_channel = None
    for d in dialogs:
        print(d.name)
        if d.name == channel_username or d.id == channel_username:
            target_channel = d
            break

    if not target_channel:
        print("未找到目标频道")
        return

    # 获取频道中的所有话题
    topics = await client(GetForumTopicsRequest(
        channel=target_channel,
        offset_date=None,
        offset_id=0,
        offset_topic=0,
        limit=100  # 可以根据需要调整
    ))

    # 找到目标话题
    target_topic = None
    for topic in topics.topics:
        print("topic.title", topic.title)
        if topic.title == subgroup_name:
            target_topic = topic
            break

    if not target_topic:
        print(f"未找到话题 {subgroup_name}")
        return

    # 获取当前时间和指定小时数之前的时间，使用 UTC 时区
    now = datetime.now(pytz.UTC)
    time_ago = now - timedelta(hours=hours_ago)

    # 获取消息
    messages = []
    offset_id = 0
    limit = 100  # 每次获取的消息数量

    while True:
        # 拿到 channel 下所有历史记录
        history = await client(GetHistoryRequest(
            peer=target_channel,
            limit=limit,
            offset_date=now,
            offset_id=offset_id,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        # 手动过滤出指定话题消息
        topic_messages = [msg for msg in history.messages 
                          if msg.reply_to 
                          and msg.reply_to.forum_topic 
                          and msg.reply_to.reply_to_msg_id == target_topic.id]

        # 过滤出指定时间范围内的消息，确保使用 UTC 时
        recent_messages = [msg for msg in topic_messages if msg.date.replace(tzinfo=pytz.UTC) > time_ago]
        messages.extend(recent_messages)

        # 如果最早的消息已经超过指定时间，就停止获取
        if topic_messages[-1].date.replace(tzinfo=pytz.UTC) <= time_ago:
            break

        offset_id = history.messages[-1].id
        if len(history.messages) < limit:
            break

    # Modify the file path to include the chat_logs directory
    chat_log_file = os.path.join("chat_logs", f"chat_logs_{channel_username}_{subgroup_name}_{now.astimezone(beijing_tz).strftime('%Y%m%d_%H%M')}.txt")

    # Update the file opening line
    with open(chat_log_file, "w", encoding="utf-8") as f:
        for message in messages:
            # 将消息时间转换为北京时间
            beijing_time = message.date.replace(tzinfo=pytz.UTC).astimezone(beijing_tz)
            f.write(f"{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}: {message.message}\n")

    print(f"最近 {hours_ago} 小时的聊天记已保存到 {chat_log_file}")

    await summarize_with_claude(chat_log_file)

# 改主程序调用，允许指定小时数
hours_to_fetch = 1
with client:
    client.loop.run_until_complete(main(hours_to_fetch))