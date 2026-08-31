import os
import chainlit as cl
import httpx
from httpx_sse import aconnect_sse

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    try:
        # رفع الـ timeout إلى 30 ثانية لضمان استقرار قراءة ملفات JSON
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with aconnect_sse(
                client,
                "POST",
                f"{BACKEND_URL}/search-stream",
                json={"query": message.content},
            ) as event_source:

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

                async for event in event_source.aiter_sse():
                    if event.data:
                        await msg.stream_token(event.data)

    except Exception as e:
        msg.content = f"⚠️ حدث خطأ أثناء الاتصال بالنظام: {str(e)}"
        await msg.update()
