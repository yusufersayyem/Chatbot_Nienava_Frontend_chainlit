import os
import chainlit as cl
import httpx
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# جلب رابط الباك إند مع التأكد من إزالة أي شَرطة مائلة زائدة في النهاية
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

@cl.on_chat_start
async def on_chat_start():
    # 1. تهيئة ذاكرة الجلسة لكل مستخدم
    cl.user_session.set("history", [])
    
    await cl.Message(
        content="المساعد الآلي للمديرية العامة لتربية نينوى .. قم بطرح أي سؤال أو استفسار لديك."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    # 2. جلب سجل المحادثة الحالي
    history = cl.user_session.get("history", [])
    
    msg = cl.Message(content="")
    await msg.send()
    
    payload = {
        "question": message.content,
        "history": history
    }
    
    full_response = ""
    target_url = f"{BACKEND_URL}/api/chat/stream"
    
    try:
        # إرسال الطلب مع مهلة زمنية 60 ثانية لتفادي انقطاع الاتصال
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", 
                target_url, 
                json=payload
            ) as response:
                
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk:
                            full_response += chunk
                            await msg.stream_token(chunk)
                else:
                    full_response = f"⚠️ خطأ في الاتصال بالسيرفر (Status {response.status_code})\nالرابط المستهدف: `{target_url}`"
                    msg.content = full_response
                    
        await msg.update()
        
        # 3. تحديث ذاكرة الجلسة عند نجاح الاستجابة
        if response.status_code == 200 and full_response:
            history.append({"role": "user", "content": message.content})
            history.append({"role": "assistant", "content": full_response})
            cl.user_session.set("history", history)
            
    except Exception as e:
        # طباعة التفاصيل الدقيقة للخطأ ونوع الاستثناء لمعرفة السبب فوراً
        error_details = (
            f"⚠️ حدث خطأ أثناء الاتصال بالخلفية:\n"
            f"- **نوع الخطأ:** `{type(e).__name__}`\n"
            f"- **تفاصيل الخطأ:** `{str(e)}`\n"
            f"- **الرابط المستهدف:** `{target_url}`"
        )
        msg.content = error_details
        await msg.update()
