import os
import httpx
import chainlit as cl

# رابط الـ Backend (سيتم استبداله برابط Render بعد النشر)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

@cl.on_message
async def main(message: cl.Message):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/search",
                json={"query": message.content}
            )

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer")
            if answer:
                await cl.Message(content=answer).send()
            else:
                await cl.Message(
                    content="عذراً، هذه المعلومة غير متوفرة في قاعدة البيانات المتاحة لدي."
                ).send()
        else:
            await cl.Message(content="حدث خطأ في الاستجابة من الخادم.").send()

    except Exception as e:
        await cl.Message(content=f"حدث خطأ أثناء الاتصال بالنظام: {str(e)}").send()
