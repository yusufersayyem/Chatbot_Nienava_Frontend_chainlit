import os
import chainlit as cl
import httpx

# رابط الباك إند - يقرأ محلياً أو من متغيرات البيئة تلقائياً
BACKEND_URL = os.getenv(
    "BACKEND_URL", "http://localhost:8000/search-stream"
)

@cl.on_chat_start
async def on_chat_start():
    """ارسال رسالة الترحيب عند فتح الشات."""
    await cl.Message(
        content=(
            "مرحباً بك! 👋\n"
            "أنا مساعد البحث الدلالي الذكي لمديرية تربية نينوى.\n"
            "كيف يمكنني مساعدتك اليوم؟"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """استقبال السؤال وقراءة النتائج بالبث المباشر (SSE Stream)."""
    user_query = message.content.strip()

    if not user_query:
        return

    # إنشاء عنصر رسالة تفاعلية جديدة للبث
    msg = cl.Message(content="")
    await msg.send()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", BACKEND_URL, json={"query": user_query}
            ) as response:

                if response.status_code != 200:
                    msg.content = (
                        f"⚠️ حدث خطأ أثناء الاتصال بالخادم الرئيسي (رمز: {response.status_code})."
                    )
                    await msg.update()
                    return

                # استقبال البث التفاعلي للكلمات وتركيبها فورياً
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line.replace("data: ", "")

                        if chunk.strip() == "[DONE]":
                            break

                        # تحويل رموز السطر الجديد النصية إلى أسطر حقيقية
                        formatted_chunk = chunk.replace("\\n", "\n")
                        await msg.stream_token(formatted_chunk)

    except Exception as e:
        msg.content = f"❌ تعذر الاتصال ببرنامج الباكإند: {str(e)}"
        await msg.update()
