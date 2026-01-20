import openai
import os

# 🔑 SET YOUR API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are a polite Indian biryani hotel assistant.
You understand English and Hinglish.
Keep replies short, friendly and helpful.
"""

def ai_reply(user_message: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message["content"]
