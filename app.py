import chainlit as cl
import httpx

# رابط خادم الـ Backend
BACKEND_URL = "http://localhost:8000/predict"

@cl.on_message
async def main(message: cl.Message):
    user_text = message.content
    
    try:
        # إرسال طلب إلى الـ Backend
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(BACKEND_URL, json={"text": user_text})
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response")
            else:
                reply = "حدث خطأ أثناء التواصل مع خادم معالجة النصوص."
                
    except httpx.RequestError:
        reply = "تعذر الاتصال بالـ Backend. تأكد من تشغيل الخادم."

    await cl.Message(content=reply).send()
