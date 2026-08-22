import os
import chainlit as cl
import httpx
from httpx_sse import aconnect_sse

# رابط الـ Backend
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

@cl.on_message
async def main(message: cl.Message):
    # إنشاء رسالة فارغة لبدء ضخ الكلمات فيها تدريجياً
    msg = cl.Message(content="")
    await msg.send()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with aconnect_sse(
                client, 
                "POST", 
                f"{BACKEND_URL}/search-stream", 
                json={"query": message.content}
            ) as event_source:
                
                async for event in event_source.aiter_sse():
                    if event.data:
                        # عرض الكلمات تدريجياً (Streaming Effect)
                        await msg.stream_token(event.data)

        # تحديث الرسالة كمنتهية بعد اكتمال النص
        await msg.update()

    except Exception as e:
        msg.content = f"حدث خطأ أثناء الاتصال بالنظام: {str(e)}"
        await msg.update()
