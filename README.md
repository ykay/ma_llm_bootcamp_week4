# Week 4 Lab Notes

One of the first issues I encountered with Milestone 4 was that I encountered a circular dependency while instructing the planning agent (base class) to delegate to the Implementation Agent. To resolve this, I implemented function calling in the main app to decide whether to call the planning or implementation agent, so there is no dependency between the agents.

The implementation seems to work more often than not for step 1, but as the steps progress, the LLM starts to bypass the agent delegation and respond as if it completed a milestone, or it will properly call the agent, but no changes will occur in the html, css, etc. (i.e., they remain the same from the previous step). I'm suspecting that the accumulation of messages in the conversation might be confusing the LLM or making the LLM "lazy" (just pretending like it implemented a milestone). 

Whatever the case, taking a closer look at how the three differen conversation histories (main, planning, implementation) grow and seeing where it starts to fall apart may help understand what is causing the agent(s) / LLM to destabilize.

# Chainlit Instructions

This project is a starter Chainlit application that demonstrates a simple integration with OpenAI's API. It showcases the following key features:

1. **OpenAI Integration**: The app is connected to OpenAI's API, allowing it to leverage state-of-the-art language models for generating responses.

2. **Streaming Responses**: Instead of waiting for the entire response to be generated, the app streams the AI's response in real-time, providing a more interactive and engaging user experience.

3. **Chat History**: The application maintains a conversation history, enabling context-aware responses and allowing for more coherent and meaningful interactions.

4. **Environment Variable Management**: Sensitive information like API keys are managed securely using environment variables.

5. **LangSmith Integration**: The app includes LangSmith for tracing and monitoring AI interactions, which can be useful for debugging and optimizing your AI application.

As a convenience, on start of a new chat session, a system prompt is added as the first message in the chat history.

## Getting Started

### 1. Create a virtual environment

First, create a virtual environment to isolate the project dependencies:
```bash
python -m venv .venv
```

### 2. Activate the virtual environment:

- On Windows:
  ```bash
  .venv\Scripts\activate
  ```
- On macOS and Linux:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

Install the project dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

- Copy the `.env.sample` file to a new file named `.env`
- Fill in the `.env` file with your API keys

## Running the app

To run the app, use the following command:

```bash
chainlit run app.py -w
``` 

## Updating dependencies

If you need to update the project dependencies, follow these steps:

1. Update the `requirements.in` file with the new package or version.

2. Install `pip-tools` if you haven't already:
   ```bash
   pip install pip-tools
   ```

3. Compile the new `requirements.txt` file:
   ```bash
   pip-compile requirements.in
   ```

4. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

This process ensures that all dependencies are properly resolved and pinned to specific versions for reproducibility.
