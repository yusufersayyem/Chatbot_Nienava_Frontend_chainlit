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
        # زِدنا الـ timeout إلى 120 ثانية للتوافق مع استجابة نموذج التفكير (Reasoning)
        async with httpx.AsyncClient(timeout=120.0) as client:

            # طلب واحد فقط لفتح اتصال SSE المباشر
            async with aconnect_sse(
                client,
                "POST",
                f"{BACKEND_URL}/search-stream",
                json={"query": message.content},
            ) as event_source:

                # التحقق المباشر من نجاح الاتصال ووجود الترويسات المناسبة
                response = event_source.response

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

                # قراءة البث المتدفق فوراً وبشكل فعال
                async for event in event_source.aiter_sse():
                    if event.data:
                        # عرض النص المتدفق تدريجياً
                        await msg.stream_token(event.data)

        # تحديث الحالة النهائية عند اكتمال البث
        await msg.update()

    except Exception as e:
        msg.content = f"⚠️ حدث خطأ أثناء الاتصال بالنظام: {str(e)}"
        await msg.update()
