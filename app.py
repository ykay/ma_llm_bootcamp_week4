from dotenv import load_dotenv
import chainlit as cl
import openai

# Load environment variables
load_dotenv()

from langsmith.wrappers import wrap_openai
from langsmith import traceable

client = wrap_openai(openai.AsyncClient())

gen_kwargs = {
    "model": "gpt-4o",
    "temperature": 0.2,
    "max_tokens": 500
}

@traceable
@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    message_history.append({"role": "user", "content": message.content})
    
    response_message = cl.Message(content="")
    await response_message.send()

    stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)

    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)
    await response_message.update()

if __name__ == "__main__":
    cl.main()
