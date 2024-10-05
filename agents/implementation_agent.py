import chainlit as cl
import json
import utils
import os
from agents.base_agent import Agent

class ImplementationAgent(Agent):

  tools = [
        {
            "type": "function",
            "function": {
                "name": "implementMilestone",
                "description": "Update an artifact file which is HTML, CSS, or markdown with the given contents. This should also be called this when an artifact (i.e., plan.md) file hasn't been created yet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "milestone": {
                            "type": "string",
                            "description": "This is the milestone number and description.",
                        },
                        "html": {
                            "type": "string",
                            "description": "<div>This is the HTML</div>",
                        },
                        "css": {
                            "type": "string",
                            "description": "div { color: red; }",
                        },
                        "plan": {
                            "type": "string",
                            "description": "This is the updated plan.md",
                        },
                    },
                    "required": ["milestone", "html", "css", "plan"],
                    "additionalProperties": False,
                },
            }
        }
    ]
  
  def __init__(self, name, client, prompt, gen_kwargs=None):
        self.name = name
        self.client = client
        self.prompt = prompt
        self.gen_kwargs = gen_kwargs or {
            "model": "gpt-4o",
            "temperature": 0.2
        }

  async def execute(self, message_history, response_message=None):
    copied_message_history = message_history.copy()

    if copied_message_history and copied_message_history[0]["role"] == "system":
        copied_message_history[0] = {"role": "system", "content": self._build_system_prompt()}
    else:
        copied_message_history.insert(0, {"role": "system", "content": self._build_system_prompt()})

    stream = await self.client.chat.completions.create(messages=copied_message_history, stream=True, tools=self.tools, tool_choice="auto", **self.gen_kwargs)
    function_array, argument_array = await utils.stream_chainlit_response_and_get_function_calls(stream, response_message)

    implementation_action_taken_context = ""
    for index, function_name in enumerate(function_array):
      if function_name:
        arguments = argument_array[index]

        print("DEBUG: functions: ", function_name)
        print("DEBUG: arguments: ", arguments)

        if function_name == "implementMilestone":
          response_message.content += "\nImplementing a milestone...\n"
          await response_message.update()
          
          arguments_dict = json.loads(arguments)
          milestone = arguments_dict.get("milestone")
          html = arguments_dict.get("html")
          css = arguments_dict.get("css")
          plan = arguments_dict.get("plan")

          os.makedirs("artifacts", exist_ok=True)
        
          with open(os.path.join("artifacts", "index.html"), "w") as file:
              file.write(html)
            
          with open(os.path.join("artifacts", "style.css"), "w") as file:
              file.write(css)

          with open(os.path.join("artifacts", "plan.md"), "w") as file:
              file.write(plan)

          implementation_action_taken_context = f"""
          Implemented milestone: {milestone}.
          Latest plan.md looks like this: 
          {plan}
          """


        
    if implementation_action_taken_context:
      message_history.append({"role": "system", "content": implementation_action_taken_context})

      stream = await self.client.chat.completions.create(messages=message_history, stream=True, **self.gen_kwargs)
      await utils.stream_chainlit_response_and_get_function_calls(stream, response_message)
      


    



    