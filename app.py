import os
import json
import httpx
import chainlit as cl

# رابط الـ Backend الخاص بك على Render
# قم باستبدال الرابط أدناه برابط الـ Backend الخاص بك
BACKEND_URL = os.environ.get("BACKEND_URL", "https://your-backend-name.onrender.com/api/chat")

@cl.on_chat_start
async def start_chat():
    # تهيئة سجل المحادثة
    cl.user_session.set("history", [])
    await cl.Message(content="مرحباً بك! كيف يمكنني مساعدتك اليوم؟").send()

@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history", [])

    # تجهيز رسالة واجهة المستخدم لبث النتيجة فيها
    msg = cl.Message(content="")
    await msg.send()

    payload = {
        "message": message.content,
        "history": history
    }

    assistant_response = ""

    try:
        # الاتصال بـ API الـ Backend واستقبال البث التدفقي (SSE)
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", BACKEND_URL, json=payload) as response:
                if response.status_code != 200:
                    await msg.stream_token("حدث خطأ في الاتصال بالخادم الرئيسي.")
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_content = line.replace("data: ", "").strip()
                        if data_content:
                            try:
                                token = json.loads(data_content)
                                assistant_response += token
                                await msg.stream_token(token)
                            except json.JSONDecodeError:
                                pass

        await msg.update()

        # تحديث سجل المحادثة المحلي
        history.append({"role": "user", "content": message.content})
        history.append({"role": "assistant", "content": assistant_response})
        cl.user_session.set("history", history)

    except Exception as e:
        msg.content = f"حدث خطأ أثناء الاتصال بالخادم: {str(e)}"
        await msg.update()
