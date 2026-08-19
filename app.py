import os
import chainlit as cl
import httpx
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="المساعد الآلي للمديرية العامة لتربية نينوى .. قم بطرح أي سؤال أو استفسار لديك."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
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
        # مهلة 120 ثانية لاستيعاب إستيقاظ السيرفر من وضع السكون
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", target_url, json=payload) as response:
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk:
                            full_response += chunk
                            await msg.stream_token(chunk)
                else:
                    full_response = f"⚠️ خطأ في الاتصال بالسيرفر (Status {response.status_code})"
                    msg.content = full_response
                    
        await msg.update()
        
        if response.status_code == 200 and full_response:
            history.append({"role": "user", "content": message.content})
            history.append({"role": "assistant", "content": full_response})
            cl.user_session.set("history", history)
            
    except Exception as e:
        msg.content = f"⚠️ حدث خطأ أثناء الاتصال بالخلفية:\n`{type(e).__name__}: {str(e)}`"
        await msg.update()
