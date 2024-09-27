from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
from datetime import date, datetime, timedelta
import pytz  # 添加这行

# 定义东八区时区
beijing_tz = pytz.timezone('Asia/Shanghai')

# 请填写您的api_id, api_hash和phone
api_id = '26421064'
api_hash = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
phone = '+12068619306'

# 目标群组的username或id
group_username = '勃勃的美股投资日报会员群'
subgroup_name = '今日行情'


client = TelegramClient('session', api_id, api_hash)

async def main(hours_ago=1):  # 添加 hours_ago 参数，默认为 1 小时
    await client.start()
    print("Client Created")

    # 获取所有对话
    dialogs = await client.get_dialogs()

    # 找到目标群组
    target_group = None
    for d in dialogs:
        print(d.name)
        if d.name == group_username or d.id == group_username:
            target_group = d
            break

    if not target_group:
        print("未找到目标群组")
        return

    # 获取群组中的所有话题
    topics = await client(GetForumTopicsRequest(
        channel=target_group,
        offset_date=None,
        offset_id=0,
        offset_topic=0,
        limit=100  # 可以根据需要调整
    ))

    # 找到目标子群组（话题）
    target_topic = None
    for topic in topics.topics:
        print("topic.title", topic.title)
        if topic.title == subgroup_name:
            target_topic = topic
            break

    if not target_topic:
        print(f"未找到子群组 {subgroup_name}")
        return

    # 获取当前时间和指定小时数之前的时间，使用 UTC 时区
    now = datetime.now(pytz.UTC)
    time_ago = now - timedelta(hours=hours_ago)

    # 获取消息
    messages = []
    offset_id = 0
    limit = 100  # 每次获取的消息数量

    while True:
        history = await client(GetHistoryRequest(
            peer=target_group,
            limit=limit,
            offset_date=now,
            offset_id=offset_id,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        # 手动过滤出指定话题的消息
        topic_messages = [msg for msg in history.messages]
        
        if not topic_messages:
            break

        # 过滤出指定时间范围内的消息，确保使用 UTC 时区
        recent_messages = [msg for msg in topic_messages if msg.date.replace(tzinfo=pytz.UTC) > time_ago]
        messages.extend(recent_messages)

        # 如果最早的消息已经超过指定时间，就停止获取
        if topic_messages[-1].date.replace(tzinfo=pytz.UTC) <= time_ago:
            break

        offset_id = history.messages[-1].id
        if len(history.messages) < limit:
            break

    # 将消息保存到文件，使用北京时间
    with open(f"chat_logs_{group_username}_{subgroup_name}_{now.astimezone(beijing_tz).strftime('%Y%m%d_%H%M')}.txt", "w", encoding="utf-8") as f:
        for message in messages:
            # 将消息时间转换为北京时间
            beijing_time = message.date.replace(tzinfo=pytz.UTC).astimezone(beijing_tz)
            f.write(f"{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}: {message.message}\n")

    print(f"最近 {hours_ago} 小时的聊天记录已保存到 chat_logs_{group_username}_{subgroup_name}_{now.astimezone(beijing_tz).strftime('%Y%m%d_%H%M')}.txt")

# 修改主程序调用，允许指定小时数
hours_to_fetch = 5  # 例如，获取最近 24 小时的记录
with client:
    client.loop.run_until_complete(main(hours_to_fetch))