import base64
import re

def extract_json_block(text):
    # Regular expression to find the content between ```json and ```
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    match = pattern.search(text)
    
    if match:
        json_str = match.group(1).strip()
        return json_str
    else:
        print("Error: No JSON block found.")
        return None
    
# Process the image if it exists, otherwise append as normal text.
def append_chainlit_message_to_history(cl_message, message_history, role):
  if imageMessage := image_message(cl_message):
    message_history.append(imageMessage)
  elif cl_message.content:
    message_history.append({"role": role, "content": cl_message.content})

def image_message(message):
    # Processing images exclusively
    images = [file for file in message.elements if "image" in file.mime] if message.elements else []

    if images:
        # Read the first image and encode it to base64
        with open(images[0].path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message.content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    
    return None

# Stream the response and return the function name and arguments (if any)
async def stream_chainlit_response_and_get_function_calls(stream, cl_response_message):
    functions = []
    arguments = []
    async for part in stream:
        if part.choices[0].delta.tool_calls:
            index = 0
            
            while index < len(part.choices[0].delta.tool_calls):
              functions.append("")
              arguments.append("")
              index += 1

            for index, tool_call in enumerate(part.choices[0].delta.tool_calls):
              functions_delta = tool_call.function.name or ""
              arguments_delta = tool_call.function.arguments or ""

              functions[index] += functions_delta
              arguments[index] += arguments_delta

        if token := part.choices[0].delta.content or "":
            await cl_response_message.stream_token(token)

    await cl_response_message.update()
    
    return functions, arguments