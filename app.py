import os
import chainlit as cl
import httpx
from dotenv import load_dotenv

load_dotenv()

# رابط الـ Backend الخاص بك على Render (أو المحلي أثناء التطوير)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@cl.on_chat_start
async def on_chat_start():
    # 1. تهيئة مصفوفة الذاكرة في جلسة المستخدم عند بدء المحادثة
    cl.user_session.set("history", [])
    
    await cl.Message(
        content="المساعد الآلي للمديرية العامة لتربية نينوى .. قم بطرح أي سؤال أو استفسار لديك."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    # 2. جلب الذاكرة الحالية من الجلسة
    history = cl.user_session.get("history", [])
    
    msg = cl.Message(content="")
    await msg.send()
    
    # تحضير جسم الطلب ليحتوي على السؤال وسجل المحادثة
    payload = {
        "question": message.content,
        "history": history
    }
    
    full_response = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", 
                f"{BACKEND_URL}/api/chat/stream", 
                json=payload
            ) as response:
                
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk:
                            full_response += chunk
                            await msg.stream_token(chunk)
                else:
                    full_response = f"⚠️ خطأ في الاتصال بالسيرفر: Status {response.status_code}"
                    msg.content = full_response
                    
        await msg.update()
        
        # 3. تحديث الذاكرة إضافة الرسالة الجديدة وإجابة البوت إليها
        if response.status_code == 200:
            history.append({"role": "user", "content": message.content})
            history.append({"role": "assistant", "content": full_response})
            cl.user_session.set("history", history)
            
    except Exception as e:
        msg.content = f"⚠️ حدث خطأ أثناء الاتصال بالخلفية: {str(e)}"
        await msg.update()
