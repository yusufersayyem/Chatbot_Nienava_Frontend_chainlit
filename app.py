import os
import json
import httpx
import chainlit as cl

# الحصول على رابط الـ Backend من متغيرات البيئة
BACKEND_URL = os.environ.get("BACKEND_URL", "https://your-backend-name.onrender.com/api/chat")

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("history", [])
    await cl.Message(content="مرحباً بك! كيف يمكنني مساعدتك اليوم؟").send()

@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history", [])

    # إنشاء رسالة فارغة لبث الاستجابة فيها
    msg = cl.Message(content="")
    await msg.send()

    payload = {
        "message": str(message.content),
        "history": history
    }

    assistant_response = ""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", BACKEND_URL, json=payload) as response:
                
                if response.status_code != 200:
                    # تحويل رقم حالة الاستجابة إلى str صراحة
                    err_msg = "حدث خطأ في الاتصال بالخادم. رمز الحالة: " + str(response.status_code)
                    msg.content = err_msg
                    await msg.update()
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_content = line.replace("data: ", "").strip()
                        
                        if data_content:
                            try:
                                token = json.loads(data_content)
                            except json.JSONDecodeError:
                                token = data_content

                            # تحويل الـ token إلى str صراحة قبل التجميع لمنع خطأ int to str
                            str_token = str(token)
                            assistant_response += str_token
                            await msg.stream_token(str_token)

        await msg.update()

        # تحديث سجل المحادثة
        history.append({"role": "user", "content": str(message.content)})
        history.append({"role": "assistant", "content": str(assistant_response)})
        cl.user_session.set("history", history)

    except Exception as e:
        # تحويل نص الخطأ إلى str صراحة
        error_text = "حدث خطأ أثناء الاتصال بالخادم: " + str(e)
        msg.content = error_text
        await msg.update()
