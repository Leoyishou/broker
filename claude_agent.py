import os
import requests
import json
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.gptsapi.net"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate_response(self, prompt, model="claude-3-sonnet-20240229", max_tokens=1000, temperature=0.7):
        endpoint = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            logger.info(f"Sending request to Claude API with prompt: {prompt[:50]}...")
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            completion = response.json().get("choices", [{}])[0].get("message", {}).get("content")
            logger.info(f"Received response from Claude API: {completion[:50]}...")
            return completion
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")
        return None

if __name__ == "__main__":
    # 加载 .env 文件
    load_dotenv()

    # 从 .env 文件获取 API 密钥
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        logger.error("Please add 'CLAUDE_API_KEY' to your .env file")
        exit(1)

    agent = ClaudeAgent(api_key)

    prompt = "你好，Claude！请帮我完成这项任务。"
    logger.info(f"Sending prompt to Claude: {prompt}")
    response = agent.generate_response(prompt)
    if response:
        logger.info("Claude's response:")
        print(response)
    else:
        logger.warning("Failed to get a response from Claude.")