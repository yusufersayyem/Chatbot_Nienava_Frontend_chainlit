import os
import chainlit as cl
import httpx
from dotenv import load_dotenv

load_dotenv()

# رابط الـ Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="المساعد الآلي للمديرية العامة لتربية نينوى وجامعة الموصل .. قم بطرح أي سؤال أو استفسار لديك."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", 
                f"{BACKEND_URL}/api/chat/stream", 
                json={"question": message.content}
            ) as response:
                
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk:
                            await msg.stream_token(chunk)
                else:
                    msg.content = f"⚠️ خطأ في الاتصال بالسيرفر: Status {response.status_code}"
                    
        await msg.update()
        
    except Exception as e:
        msg.content = f"⚠️ حدث خطأ أثناء الاتصال بالخلفية: {str(e)}"
        await msg.update()
