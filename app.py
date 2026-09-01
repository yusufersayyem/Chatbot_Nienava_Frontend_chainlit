import os
import chainlit as cl
import httpx

# رابط الباكإند على Render (يُقرأ تلقائياً من Environment Variables أو يوضع افتراضياً)
BACKEND_URL = os.getenv(
    "BACKEND_URL", "https://your-fastapi-app.onrender.com/search-stream"
)


@cl.on_chat_start
async def on_chat_start():
  """ترسيل رسالة الترحيب عند فتح الشات."""
  await cl.Message(
      content=(
          "مرحباً بك! 👋\nأنا مساعد البحث الدلالي الذكي لمديرية تربية"
          " نينوى.\nكيف يمكنني مساعدتك اليوم؟"
      )
  ).send()


@cl.on_message
async def on_message(message: cl.Message):
  """استقبال السؤال وقراءة النتائج بالبث المباشر (SSE Stream)."""
  user_query = message.content.strip()

  # إنشاء عنصر رسالة تفاعلية جديدة
  msg = cl.Message(content="")
  await msg.send()

  try:
    # استخدام AsyncClient مع مهلة زمنية تتسع لمعالجة البيانات
    async with httpx.AsyncClient(timeout=60.0) as client:
      async with client.stream(
          "POST", BACKEND_URL, json={"query": user_query}
      ) as response:

        if response.status_code != 200:
          msg.content = (
              f"⚠️ حدث خطأ أثناء الاتصال بالخادم الرئيسي (رمز:"
              f" {response.status_code})."
          )
          await msg.update()
          return

        # استقبال البث التفاعلي للكلمات وتركيبها فورياً
        async for line in response.aiter_lines():
          if line.startswith("data: "):
            chunk = line.replace("data: ", "")

            if chunk.strip() == "[DONE]":
              break

            await msg.stream_token(chunk)

  except Exception as e:
    msg.content = f"❌ تعذر الاتصال ببرنامج الباكإند: {str(e)}"
    await msg.update()
