import os
import json
import httpx
import chainlit as cl

# ضع رابط الـ Backend الخاص بك هنا بعد نشره
BACKEND_URL = os.environ.get("BACKEND_URL", "https://https://chatbot-nienava-backend-chainlit.onrender.com/api/chat")

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("history", [])
    await cl.Message(content="مرحباً بك! كيف يمكنني مساعدتك اليوم؟").send()

@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history", [])

    msg = cl.Message(content="")
    await msg.send()

    payload = {
        "message": message.content,
        "history": history
    }

    assistant_response = ""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", BACKEND_URL, json=payload) as response:
                if response.status_code != 200:
                    await msg.stream_token("حدث خطأ في الاتصال بالسيرفر الرئيسي.")
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_content = line.replace("data: ", "").strip()
                        if data_content:
                            try:
                                token = json.loads(data_content)
                            except json.JSONDecodeError:
                                token = data_content

                            assistant_response += token
                            await msg.stream_token(token)

        await msg.update()

        history.append({"role": "user", "content": message.content})
        history.append({"role": "assistant", "content": assistant_response})
        cl.user_session.set("history", history)

    except Exception as e:
        msg.content = f"حدث خطأ أثناء الاتصال بالخادم: {str(e)}"
        await msg.update()
