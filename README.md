# Curator

Curator is an LLM-powered art curation agent designed to search and utilize various tools based on user requests. It operates on a Raspian system and leverages a combination of Linux commands, custom scripts, and LLM requests to manage and create art.

## Features

- Intelligent art curation and management
- Utilizes Linux commands, custom scripts, and LLM requests
- File-based approach for problem-solving
- Extensible tool system

## Directory Structure

```
~/pi_boss/
├── scripts/
│   ├── custom_python_scripts.py
│   └── custom_bash_scripts.sh
├── prompts/
│   └── prompt_templates.txt
└── tool_cache.json
```

## Usage

1. Start the Curator agent
2. Input your art-related requests
3. The agent will process your request, select appropriate tools, and execute actions
4. Results will be returned to you or used for further processing as needed

## Extending Curator

### Adding Custom Scripts

1. Create a new Python (.py) or Bash (.sh) script in the `~/pi_boss/scripts/` directory
2. Include a detailed docstring explaining the script's functionality and usage
3. The script will automatically be discovered and added to the tool cache

### Adding LLM Prompts

1. Create a new text file (.txt) in the `~/pi_boss/prompts/` directory
2. Include a description and usage information at the beginning of the file
3. Write the prompt template in the file
4. The new prompt will be automatically discovered and added to the tool cache

## Dependencies
TODO