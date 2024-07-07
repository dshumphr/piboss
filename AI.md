# Curator

An LLM-powered art curation agent that is able to search and use tools based on user requests.

Tools include common linux scripts, custom scripts, and LLM requests (which may use reusable prompt templates). 
Th custom scripts and LLM scripts largely center around art creation and display.

The agent is powered by Python and frequently uses a files-based approach to solving problems.

## Plan

1. Tool Discovery and Management:
   a. Linux commands:
      - Simply inform the LLM this is a Raspian system.
   b. Custom scripts:
      - Store in a dedicated folder: `~/pi_boss/scripts/`
   c. LLM requests:
      - Store prompt templates in `~/pi_boss/prompts/`

2. Tool Information:
   a. Linux commands:
      - Use `man` command to fetch detailed information when needed. This should be rare.
   b. Custom scripts:
      - Store detailed information in script docstrings.
   c. LLM requests:
      - Store description and usage in the prompt template files.

3. Caching Tools:
    a. Cache all tool names and usage info in a file

3. Execution Loop:
   a. Call LLM:
      - Parse user request and ask LLM to identify required tools or actions
      - Ensure the LLM specifies whether to return tool results to the LLM or the user
   b. Handle response
      - Execute any selected tools and send results to LLM or user, as specified.
      - Break if nothing left to send to LLM and wait for more user input
    Ensure loop is interuptable by user, resulting in ending any commands/llm requests

4. Tool Creation:
   a. Python scripts:
      - Create new .py files in `~/pi_boss/scripts/`
   b. Bash scripts:
      - Create new .sh files in `~/pi_boss/scripts/`
   c. LLM prompts:
      - Create new .txt files in `~/pi_boss/prompts/`
