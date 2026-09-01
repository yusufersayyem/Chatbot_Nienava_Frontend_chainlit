import json
import os
import chainlit as cl
import httpx

# ==========================================
# 1. إعداد رابط API الخاص بالسيرفر
# ==========================================
# استبدل هذا الرابط برابط سيرفر FastAPI الخاص بك على Render
BACKEND_URL = os.getenv(
    "BACKEND_URL", "https://your-fastapi-app.onrender.com/search-stream"
)


# ==========================================
# 2. أحداث Chainlit (واجهة المستخدم)
# ==========================================


@cl.on_chat_start
async def on_chat_start():
  """ترسيل رسالة ترحيبية عند فتح واجهة المحادثة."""
  await cl.Message(
      content=(
          "مرحباً بك! 👋\nأنا مساعد البحث الدلالي الخاص بمديرية تربية"
          " نينوى.\nكيف يمكنني مساعدتك اليوم؟"
      )
  ).send()


@cl.on_message
async def on_message(message: cl.Message):
  """استقبال الاستفسار من المستخدم وإرساله لسيرفر FastAPI مع بث الإجابة (Streaming)."""
  user_query = message.content.strip()

  # إنشاء رسالة فارغة ليبدأ بث النص فيها تدريجياً
  msg = cl.Message(content="")
  await msg.send()

  # إرسال طلب إلى الباكإند وقراءة البث (SSE)
  try:
    async with httpx.AsyncClient(timeout=60.0) as client:
      async with client.stream(
          "POST", BACKEND_URL, json={"query": user_query}
      ) as response:
        if response.status_code != 200:
          msg.content = f"⚠️ حدث خطأ في الاتصال بالخادم: {response.status_code}"
          await msg.update()
          return

        # قراءة النص المتدفق وإضافته للرسالة خطوة بخطوة
        async for line in response.aiter_lines():
          if line.startswith("data: "):
            chunk = line.replace("data: ", "")

            # التوقف إذا وصلنا لنهاية البث أو رمز الإغلاق
            if chunk.strip() == "[DONE]":
              break

            # إضافة الكلمات الجديدة ورسمها في الواجهة فوراً
            await msg.stream_token(chunk)

  except Exception as e:
    msg.content = f"❌ تعذر الاتصال بالخادم: {str(e)}"
    await msg.update()
