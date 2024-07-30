import anthropic
import os
import subprocess
from typing import List, Dict
import json
import logging
import sys
import argparse
import random

class PiBossAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.tools_cache_file = os.path.expanduser("~/pi_boss/tools_cache.json")
        self.tools = self.load_tools()
        
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler("pi_boss_conversations.log"),
                                logging.StreamHandler()
                            ])
        
    def load_tools(self, force=False) -> Dict[str, callable]:
        logging.info("Loading tools...")
        if not force and os.path.exists(self.tools_cache_file):
            with open(self.tools_cache_file, 'r') as f:
                tools = json.load(f)
                logging.info(f"Loaded {len(tools)} tools from cache.")
                return tools
        
        tools = {}
        
        # Ensure pi_boss directories exist
        for dir_path in ["~/pi_boss/scripts", "~/pi_boss/prompts"]:
            os.makedirs(os.path.expanduser(dir_path), exist_ok=True)
        
        # Load custom scripts
        script_dir = os.path.expanduser("~/pi_boss/scripts")
        for filename in os.listdir(script_dir):
            if filename.endswith((".py", ".sh")):
                module_name = filename[:-3]
                script_path = os.path.join(script_dir, filename)
                if filename.endswith('.py'):
                    with open(script_path, 'r') as f:
                        docstring = self.extract_docstring(f.read())
                    tools[filename] = {
                        "type": "python_script",
                        "path": script_path,
                        "help": docstring
                    }
                else:
                    # Extract docstring for bash script
                    with open(script_path, 'r') as f:
                        content = f.read()
                        lines = content.split('\n')
                        docstring = ""
                        for line in lines:
                            if line.strip().startswith('#'):
                                docstring += line.strip()[1:].strip() + "\n"
                            else:
                                break
                    tools[filename] = {
                        "type": "bash_script",
                        "path": script_path,
                        "help": docstring.strip() or f"Bash script: {filename}"
                    }
                logging.info(f"Loaded script: {filename}")
        
        # Load LLM prompts
        prompt_dir = os.path.expanduser("~/pi_boss/prompts")
        for filename in os.listdir(prompt_dir):
            if filename.endswith(".txt"):
                prompt_name = filename[:-4]
                with open(os.path.join(prompt_dir, filename), 'r') as f:
                    prompt_content = f.read()
                    prompt_help = prompt_content.split('\n\n', 1)[0]  # First paragraph as help
                tools[prompt_name] = {
                    "type": "llm_prompt",
                    "content": prompt_content,
                    "help": prompt_help
                }
                logging.info(f"Loaded prompt: {filename}")
        
        # Cache the tools
        with open(self.tools_cache_file, 'w') as f:
            json.dump(tools, f)
        
        logging.info(f"Loaded and cached {len(tools)} tools.")
        return tools
    
    def extract_docstring(self, script_content):
        import ast
        try:
            tree = ast.parse(script_content)
            return ast.get_docstring(tree) or "No docstring available"
        except:
            return "Unable to parse script for docstring"

    def run(self, single_run=False, initial_prompt=None):
        while True:
            try:
                if initial_prompt:
                    user_input = initial_prompt
                    initial_prompt = None  # Clear it after first use
                else:
                    user_input = input("How can I help you today? ")
                    logging.info(f"User input: {user_input}")
                    if user_input.lower() == "exit":
                        break
                    elif user_input.lower() == "reload tools":
                        self.tools = self.load_tools(True)
                        print("Tools reloaded successfully.")
                        continue
                
                response = self.process_request(user_input)
                print("\n")
                print(response)
                logging.info(f"Response to user: {response}")
                if single_run:
                    break
            except KeyboardInterrupt:
                print("\nExecution interrupted. Stopping any ongoing processes...")
                logging.warning("Execution interrupted by user.")
                # Add logic here to stop any ongoing processes if needed
                break

    def process_request(self, user_input: str) -> str:
        logging.info(f"Processing request: {user_input}")
        tool_help_info = "\n".join([f"{name}: {info['help']}" for name, info in self.tools.items()])
        system_msg = ("You are an AI assistant that helps process user requests on a Raspbian system. "
                      "You may either respond directly or return a command to run, depending on which will provide a better user experience. "
                      "The requests typically revolve around ai art creation and display. "
                      "Please structure your responses using XML tags. Use <thought> tags for your reasoning, "
                      "<tool> tags if you specify a tool/command to use, or "
                      "<response> tags if you want to respond to the user. Multiple tools can be composed "
                      "a single Linux command in the usual ways (eg. piping). Tools include common Linux commands "
                      f"and the following tools:\n<tools>{tool_help_info}</tools>"
                      "Always start by explaining common missteps someone might make in attempting the task in <thought> tags."
                      "\n\n")
        
        messages = [
            {"role": "user", "content": f"<request>{user_input}</request>\n\n"
                                         f"How should I approach this request?"}
        ]

        while True:
            logging.debug(f"Sending request to LLM with messages: {messages}")
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620", # Note: DO NOT CHANGE THE MODEL STRING
                max_tokens=4000,
                messages=messages,
                system=system_msg,
            )

            ai_response = response.content[0].text
            logging.debug(f"LLM response: {ai_response}")
            
            thought = self.extract_tag_content(ai_response, "thought")
            tool = self.extract_tag_content(ai_response, "tool")
            response_text = self.extract_tag_content(ai_response, "response")
            
            logging.info(f"Extracted - Thought: {thought}, Tool: {tool}, Response: {response_text}")
            
            if tool:
                tool_name = tool.split()[0]
                tool_args = ' '.join(tool.split()[1:])
                if tool_name in self.tools:
                    logging.info(f"Executing tool: {tool_name}")
                    tool_info = self.tools[tool_name]
                    if tool_info["type"] == "python_script":
                        tool_result = subprocess.check_output(f"python3 {tool_info['path']} {tool_args}", shell=True, text=True)
                    elif tool_info["type"] == "bash_script":
                        tool_result = subprocess.check_output(f"bash {tool_info['path']} {tool_args}", shell=True, text=True)
                    elif tool_info["type"] == "llm_prompt":
                        tool_result = self.client.messages.create(
                            model="claude-3-sonnet-20240229",
                            max_tokens=1000,
                            messages=[{"role": "user", "content": tool_info['content']}]
                        ).content[0].text
                    logging.debug(f"Tool result: {tool_result}")
                    return f"Thought: {thought}\nTool used: {tool}\nTool result: {tool_result}\nResponse: {response_text}"
                else:
                    try:
                        logging.info(f"Executing command: {tool}")
                        tool_result = subprocess.check_output(tool, shell=True, text=True, stderr=subprocess.STDOUT)
                        logging.debug(f"Command result: {tool_result}")
                        return f"Thought: {thought}\nCommand used: {tool}\nCommand result: {tool_result}\nResponse: {response_text}"
                    except subprocess.CalledProcessError as e:
                        error_msg = f"Error: Command '{tool}' failed with error: {e.output}"
                        logging.error(error_msg)
                        return error_msg
            else:
                return f"Thought: {thought}\nResponse: {response_text}"

    def extract_tag_content(self, text: str, tag: str) -> str:
        start_tag = f"<{tag}>"
        end_tag = f"</{tag}>"
        start_index = text.find(start_tag)
        end_index = text.find(end_tag)
        if start_index != -1 and end_index != -1:
            return text[start_index + len(start_tag):end_index].strip()
        return ""

    def create_tool(self, tool_type: str, tool_name: str, tool_content: str):
        logging.info(f"Creating tool: {tool_name} of type {tool_type}")
        if tool_type == "python":
            file_path = os.path.expanduser(f"~/pi_boss/scripts/{tool_name}.py")
        elif tool_type == "bash":
            file_path = os.path.expanduser(f"~/pi_boss/scripts/{tool_name}.sh")
        elif tool_type == "prompt":
            file_path = os.path.expanduser(f"~/pi_boss/prompts/{tool_name}.txt")
        else:
            error_msg = f"Error: Invalid tool type '{tool_type}'"
            logging.error(error_msg)
            return error_msg

        with open(file_path, 'w') as f:
            f.write(tool_content)

        self.tools = self.load_tools(True)  # Reload tools after creating a new one
        success_msg = f"Tool '{tool_name}' of type '{tool_type}' created successfully."
        logging.info(success_msg)
        return success_msg

    def record_common_tasks(self, num_tasks=10):
        common_tasks = [
            "Paint a cyberpunk pyramid",
            "Draw an animal",
            "Create an oil painting",
            "Paint something lame",
            "Draw something badass",
            "Make a slideshow of cyberpunk architecture",
            "Show the dog image from last week",
            "Generate a surreal landscape",
            "Create a digital portrait",
            "Design a futuristic city skyline",
            "Illustrate a fantasy creature",
            "Compose an abstract artwork",
            "Sketch a vintage car",
            "Paint a post-apocalyptic scene",
            "Draw a steampunk invention"
        ]

        responses = []
        for _ in range(num_tasks):
            task = random.choice(common_tasks)
            logging.info(f"Recording response for task: {task}")
            response = self.process_request(task)
            responses.append({"task": task, "response": response})

        with open("common_tasks_responses.json", "w") as f:
            json.dump(responses, f, indent=2)

        logging.info(f"Recorded responses for {num_tasks} common tasks.")
        return f"Recorded responses for {num_tasks} common tasks. Results saved in common_tasks_responses.json"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PiBoss Agent")
    parser.add_argument("--single", action="store_true", help="Run the agent once and exit")
    parser.add_argument("--record-tasks", type=int, metavar="N", help="Record responses for N common tasks")
    parser.add_argument("prompt", nargs="?", help="Initial prompt for the agent")
    args = parser.parse_args()

    agent = PiBossAgent()

    if args.record_tasks:
        result = agent.record_common_tasks(args.record_tasks)
        print(result)
    else:
        agent.run(single_run=args.single, initial_prompt=args.prompt)