import os
import chainlit as cl
import json
import utils

from langfuse.decorators import observe

class Agent:
    """
    Base class for all agents.
    """

    tools = [
        {
            "type": "function",
            "function": {
                "name": "updateArtifact",
                "description": "Update an artifact file which is HTML, CSS, or markdown with the given contents. This should also be called this when an artifact (i.e., plan.md) file hasn't been created yet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to update.",
                        },
                        "contents": {
                            "type": "string",
                            "description": "The markdown, HTML, or CSS contents to write to the file.",
                        },
                    },
                    "required": ["filename", "contents"],
                    "additionalProperties": False,
                },
            }
        }
    ]

    def __init__(self, name, client, prompt="", gen_kwargs=None):
        self.name = name
        self.client = client
        self.prompt = prompt
        self.gen_kwargs = gen_kwargs or {
            "model": "gpt-4o",
            "temperature": 0.2
        }

    async def execute(self, message_history, response_message=None):
        """
        Executes the agent's main functionality.

        Note: probably shouldn't couple this with chainlit, but this is just a prototype.
        """
        copied_message_history = message_history.copy()

        # Check if the first message is a system prompt
        if copied_message_history and copied_message_history[0]["role"] == "system":
            # Replace the system prompt with the agent's prompt
            copied_message_history[0] = {"role": "system", "content": self._build_system_prompt()}
        else:
            # Insert the agent's prompt at the beginning
            copied_message_history.insert(0, {"role": "system", "content": self._build_system_prompt()})

        stream = await self.client.chat.completions.create(messages=copied_message_history, stream=True, tools=self.tools, tool_choice="auto", **self.gen_kwargs)
        function_array, argument_array = await utils.stream_chainlit_response_and_get_function_calls(stream, response_message)
        
        planning_action_taken_context = ""
        for index, function_name in enumerate(function_array):
            if function_name:
                arguments = argument_array[index]
                
                print("DEBUG: function_name: ", function_name)
                print("DEBUG: arguments: ", arguments)
                
                if function_name == "updateArtifact":                
                    response_message.content += "Updating the artifact...\n"
                    await response_message.update()

                    arguments_dict = json.loads(arguments)
                    filename = arguments_dict.get("filename")
                    contents = arguments_dict.get("contents")
                    
                    if filename and contents:
                        os.makedirs("artifacts", exist_ok=True)
                        with open(os.path.join("artifacts", filename), "w") as file:
                            file.write(contents)
                        
                        planning_action_taken_context = f"The artifact '{filename}' was updated."



        if planning_action_taken_context: # Notify user the result of the planning action
            message_history.append({"role": "system", "content": planning_action_taken_context})
            stream = await self.client.chat.completions.create(messages=message_history, stream=True, **self.gen_kwargs)
            await utils.stream_chainlit_response_and_get_function_calls(stream, response_message)


    def _build_system_prompt(self):
        """
        Builds the system prompt including the agent's prompt and the contents of the artifacts folder.
        """
        artifacts_content = "<ARTIFACTS>\n"
        artifacts_dir = "artifacts"

        if os.path.exists(artifacts_dir) and os.path.isdir(artifacts_dir):
            for filename in os.listdir(artifacts_dir):
                file_path = os.path.join(artifacts_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "r") as file:
                        file_content = file.read()
                        artifacts_content += f"<FILE name='{filename}'>\n{file_content}\n</FILE>\n"
        
        artifacts_content += "</ARTIFACTS>"

        return f"{self.prompt}\n{artifacts_content}"