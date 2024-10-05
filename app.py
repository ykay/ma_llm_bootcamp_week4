from dotenv import load_dotenv
import chainlit as cl
import prompts
import json
import os

load_dotenv()

from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI

client = AsyncOpenAI()

gen_kwargs = {"model": "gpt-4o", "temperature": 0.2}

tools = [
    {
        "type": "function",
        "function": {
            "name": "callAgent",
            "description": "Call another agent to perform a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agentName": {
                        "type": "string",
                        "description": """
                        The name of the agent to call. Available agents: 
                        - planning: Generates a plan for building a web page from an image. Call this function when the user confirms the plan is good.
                        - implementation: Implements a specific milestone in the plan.",
                        """,
                    }
                },
                "required": ["agentName"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "noAction",
            "description": "No action is needed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]

import agents.base_agent as base_agent
from agents.implementation_agent import ImplementationAgent
import utils

# Create an instance of the Agent class
planning_agent = base_agent.Agent(
    name="Planning Agent", client=client, prompt=prompts.PLANNING_PROMPT
)
implementation_agent = ImplementationAgent(
    name="Implementation Agent", client=client, prompt=prompts.IMPLEMENTATION_PROMPT
)

def initialize():
    artifacts_dir = "artifacts"
    filename = "plan.md"
    print("DEBUG: Initializing...")
    # Delete existing plan for simplifications (ability to resume previous plan complicates the implementation)
    if os.path.exists(artifacts_dir) and os.path.isdir(artifacts_dir):
        for filename in os.listdir(artifacts_dir):
            file_path = os.path.join(artifacts_dir, filename)
            if os.path.isfile(file_path) and filename == "plan.md":
                os.remove(file_path)

initialize()


@observe
@cl.on_chat_start
def on_chat_start():
    message_history = [{"role": "system", "content": prompts.SYSTEM_PROMPT}]
    cl.user_session.set("message_history", message_history)


@observe
async def generate_response(client, message_history, gen_kwargs):
    response_message = cl.Message(content="")
    await response_message.send()

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **gen_kwargs
    )
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)

    await response_message.update()

    return response_message


@cl.on_message
@observe
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    response_message = cl.Message(content="")
    await response_message.send()

    utils.append_chainlit_message_to_history(message, message_history, "user")

    stream = await client.chat.completions.create(
        messages=message_history,
        stream=True,
        tools=tools,
        tool_choice="required",
        **gen_kwargs,
    )

    # Prompt if any agent needs to be called
    function_array, argument_array = await utils.stream_chainlit_response_and_get_function_calls(stream, response_message)
    utils.append_chainlit_message_to_history(response_message, message_history, "assistant") # Only if there was a response message

    print("DEBUG: functions: ", function_array)
    for index, function_name in enumerate(function_array):
        if function_name:
            arguments = argument_array[index]

            print("DEBUG: function_name: ", function_name)
            print("DEBUG: arguments: ", arguments)
            
            if function_name == "callAgent":
                arguments_dict = json.loads(arguments)
                agent_name = arguments_dict.get("agentName")

                if agent_name:
                    response_message.content = f"Calling agent: {agent_name}...\n"
                    await response_message.update()

                    if agent_name == "planning":
                        await planning_agent.execute(message_history, response_message)
                    elif agent_name == "implementation":
                        await implementation_agent.execute(
                            message_history, response_message
                        )

                    utils.append_chainlit_message_to_history(response_message, message_history, "assistant")
                else:
                    print("DEBUG: No agent specified")
                    

    cl.user_session.set("message_history", message_history)


if __name__ == "__main__":
    cl.main()
