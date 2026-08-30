import os
import chainlit as cl
import httpx
from httpx_sse import aconnect_sse

# رابط الـ Backend
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

@cl.on_message
async def main(message: cl.Message):
    # إنشاء رسالة فارغة لبدء ضخ الحروف فيها تدريجياً
    msg = cl.Message(content="")
    await msg.send()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # فحص الاستجابة أولاً لضمان حالة HTTP 200 ووجود ترويسة text/event-stream
            async with client.stream(
                "POST",
                f"{BACKEND_URL}/search-stream",
                json={"query": message.content}
            ) as response:

                if response.status_code != 200:
                    await response.aread()
                    msg.content = f"⚠️ خطأ من السيرفر (كود {response.status_code}):\n```\n{response.text}\n```"
                    await msg.update()
                    return

                content_type = response.headers.get("content-type", "")
                if "text/event-stream" not in content_type:
                    await response.aread()
                    msg.content = f"⚠️ استجابة غير متوافقة من السيرفر (ليست Stream):\n{response.text}"
                    await msg.update()
                    return

                # ربط الاستجابة المؤكدة بـ aconnect_sse للمُعالجة التدريجية
                async with aconnect_sse(
                    client,
                    "POST",
                    f"{BACKEND_URL}/search-stream",
                    json={"query": message.content}
                ) as event_source:
                    async for event in event_source.aiter_sse():
                        if event.data:
                            # عرض النص المتدفق تدريجياً (Streaming)
                            await msg.stream_token(event.data)

        # تحديث الرسالة بعد اكتمال النص بالكامل
        await msg.update()

    except Exception as e:
        msg.content = f"حدث خطأ أثناء الاتصال بالنظام: {str(e)}"
        await msg.update()
