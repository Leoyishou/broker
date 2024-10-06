import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import asyncio
import nest_asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from typing import List, Optional
import pytz
import os
from dotenv import load_dotenv
from services.segmentation_service import SegmentationService

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Define the Beijing timezone
beijing_tz = pytz.timezone('Asia/Shanghai')

# Telegram client configuration
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = '勃勃的美股投资日报会员群'

# Define data models
class Topic:
    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title

class Message:
    def __init__(self, date: datetime, message: str):
        self.date = date
        self.message = message

async def get_topics(client):
    dialogs = await client.get_dialogs()
    target_channel = next((d for d in dialogs if d.name == channel_username), None)

    if not target_channel:
        st.error("Channel not found")
        return []

    topics = await client(GetForumTopicsRequest(
        channel=target_channel,
        offset_date=None,
        offset_id=0,
        offset_topic=0,
        limit=1000
    ))

    return [Topic(id=topic.id, title=topic.title) for topic in topics.topics]

async def fetch_messages(client, topic_id: Optional[int] = None, time_range: Optional[dict] = None):
    dialogs = await client.get_dialogs()
    target_channel = next((d for d in dialogs if d.name == channel_username), None)

    if not target_channel:
        st.error("Channel not found")
        return []

    messages = []
    offset_id = 0
    while True:
        history = await client(GetHistoryRequest(
            peer=target_channel,
            limit=100,
            offset_date=None,
            offset_id=offset_id,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        if not history.messages:
            break

        print(f"Fetched {len(history.messages)} messages")
   
        i = 0
        for message in history.messages:
            if topic_id is None or (
                hasattr(message, 'reply_to') and 
                message.reply_to and 
                message.reply_to.forum_topic and 
                (message.reply_to.reply_to_msg_id == topic_id or 
                 (hasattr(message.reply_to, 'reply_to_top_id') and message.reply_to.reply_to_top_id == topic_id))
            ):
                if time_range:
                    if time_range['start'] <= message.date <= time_range['end']:
                        messages.append(Message(date=message.date, message=message.message))
                        i += 1
                else:
                    messages.append(Message(date=message.date, message=message.message))
                    i += 1
        offset_id = history.messages[-1].id
        if i == 0:
            break

    return messages

async def main():
    st.title("Telegram Message Fetcher")

    # Initialize the Telegram client inside the main function
    client = TelegramClient('session_name', api_id, api_hash)
    try:
        await client.start()

        # Initialize session state for topics if it doesn't exist
        if 'topics' not in st.session_state:
            st.session_state.topics = []

        # Fetch and display topics
        if st.button("Load Topics") or st.session_state.topics:
            if not st.session_state.topics:
                with st.spinner("Fetching topics..."):
                    st.session_state.topics = await get_topics(client)
            
            if st.session_state.topics:
                topic_options = {topic.title: topic.id for topic in st.session_state.topics}
                selected_topic_title = st.selectbox("Select a Topic", list(topic_options.keys()), key='topic_selector')
                selected_topic_id = topic_options[selected_topic_title]
                st.session_state['selected_topic_id'] = selected_topic_id
                st.session_state['selected_topic_title'] = selected_topic_title
                
                st.write(f"Selected Topic: {selected_topic_title}")
            else:
                st.write("No topics found.")

        # Check if a topic is selected
        if 'selected_topic_id' in st.session_state:
            selected_topic_id = st.session_state['selected_topic_id']
            selected_topic_title = st.session_state['selected_topic_title']

            now = datetime.now(beijing_tz)
            one_hour_ago = now - timedelta(hours=1)

            # Initialize session state for date and time if not exists
            if 'start_date' not in st.session_state:
                st.session_state.start_date = one_hour_ago.date()
            if 'start_time' not in st.session_state:
                st.session_state.start_time = one_hour_ago.time()
            if 'end_date' not in st.session_state:
                st.session_state.end_date = now.date()
            if 'end_time' not in st.session_state:
                st.session_state.end_time = now.time()

            start_date = st.date_input("Start Date", st.session_state.start_date, key="start_date")
            start_time = st.time_input("Start Time", st.session_state.start_time, key="start_time")
            end_date = st.date_input("End Date", st.session_state.end_date, key="end_date")
            end_time = st.time_input("End Time", st.session_state.end_time, key="end_time")

            # Update session state only if the values have changed
            if start_date != st.session_state.start_date:
                st.session_state.start_date = start_date
            if start_time != st.session_state.start_time:
                st.session_state.start_time = start_time
            if end_date != st.session_state.end_date:
                st.session_state.end_date = end_date
            if end_time != st.session_state.end_time:
                st.session_state.end_time = end_time

            start_datetime = datetime.combine(start_date, start_time).replace(tzinfo=beijing_tz).astimezone(pytz.UTC)
            end_datetime = datetime.combine(end_date, end_time).replace(tzinfo=beijing_tz).astimezone(pytz.UTC)

            if st.button("Fetch Messages"):
                with st.spinner("Fetching messages..."):
                    time_range = {'start': start_datetime, 'end': end_datetime}
                    messages = await fetch_messages(client, topic_id=selected_topic_id, time_range=time_range)
                if messages:
                    st.write(f"Found {len(messages)} messages.")
                    
                    # Create a text file with the messages and segmented words
                    chat_log_dir = 'chat_log'
                    os.makedirs(chat_log_dir, exist_ok=True)
                    filename = f"messages_{selected_topic_title}_{start_datetime.astimezone(beijing_tz).strftime('%Y%m%d_%H%M')}_to_{end_datetime.astimezone(beijing_tz).strftime('%Y%m%d_%H%M')}.txt"
                    filepath = os.path.join(chat_log_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write("Chat History:\n\n")
                        for msg in messages:
                            f.write(f"{msg.date.astimezone(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')}: {msg.message}\n")
                        
                        segmentation_service = SegmentationService()
                        words = segmentation_service.segment_and_add_to_anki('\n'.join([msg.message for msg in messages]), filename, "cognition", "cognitive_vocabulary")
                        f.write(', '.join(words))

                        st.write(f"Added {len(words)} words to Anki.")
                    
                    # Provide a download link for the file
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            label="Download Messages and Segmented Words",
                            data=f,
                            file_name=filename,
                            mime="text/plain"
                        )
                else:
                    st.write("No messages found in the specified time range.")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())