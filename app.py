import os
import requests
import chainlit as cl

# رابط الـ Backend (سيتم استبداله برابط Render عند النشر)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/predict")

@cl.on_message
async def main(message: cl.Message):
    user_text = message.content
    
    try:
        # إرسال طلب للـ Backend
        response = requests.post(
            BACKEND_URL,
            json={"text": user_text},
            timeout=10
        )
        
        if response.status_code == 200:
            bot_response = response.json().get("response")
        else:
            bot_response = "حدث خطأ أثناء الاتصال بالخادم."
            
    except Exception as e:
        bot_response = "تعذر الاتصال بالخادم. يرجى التحقق من تشغيل Backend."

    await cl.Message(content=bot_response).send()
