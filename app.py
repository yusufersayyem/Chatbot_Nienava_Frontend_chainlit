import json
import os
import chainlit as cl
import httpx

# رابط الباك إند - يقرأ من متغير البيئة على Render أو localhost للتطوير المحلي
BACKEND_URL = os.getenv(
    "BACKEND_URL", "http://localhost:8000/search-stream"
)


@cl.on_chat_start
async def on_chat_start():
    """إرسال رسالة الترحيب عند فتح الشات."""
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
        # زيادة Timeout لـ 90 ثانية لتفادي انقطاع الاتصال عند استيقاظ نموذج HF
        async with httpx.AsyncClient(timeout=90.0) as client:
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
                        raw_data = line.replace("data: ", "").strip()

                        if raw_data == "[DONE]":
                            break

                        # استخراج النص بدمج آمن يضمن عرض الأحرف العربية بدون تشويه
                        chunk_text = raw_data
                        try:
                            parsed_json = json.loads(raw_data)
                            if isinstance(parsed_json, dict) and "data" in parsed_json:
                                chunk_text = parsed_json["data"]
                            elif isinstance(parsed_json, str):
                                chunk_text = parsed_json
                        except json.JSONDecodeError:
                            pass

                        # تحويل رموز السطر الجديد النصية إلى أسطر حقيقية
                        formatted_chunk = chunk_text.replace("\\n", "\n")
                        await msg.stream_token(formatted_chunk)

    except httpx.ReadTimeout:
        msg.content = "⏳ استغرق الخادم وقتاً أطول من المتوقع للاستجابة. يرجى إعادة المحاولة."
        await msg.update()
    except Exception as e:
        msg.content = f"❌ تعذر الاتصال بالباك إند: {str(e)}"
        await msg.update()
