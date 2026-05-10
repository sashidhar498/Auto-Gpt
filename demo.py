import regex as re
import json
import os
import subprocess
import shutil
import logging
from dotenv import load_dotenv
load_dotenv()

from openrouter import OpenRouter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_json_loads(text):
    """Safely parses JSON from LLM responses. Handles markdown, control characters, and malformed JSON."""
    if not text:
        raise ValueError("Empty response text")
    
    text = text.strip()
    
    # Remove markdown code blocks
    for marker in ["", "", "python"]:
        text = text.replace(marker, "")
    
    # Try to find JSON object/array
    # Handle both {"key": ...} and [{"key": ...}]
    text = text.strip()
    if text.startswith("["):
        match = re.search(r'\[.*\]', text, re.DOTALL)
    else:
        match = re.search(r'\{.*\}', text, re.DOTALL)
    
    if not match:
        # Try to find any JSON-like structure
        match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
    
    if not match:
        raise ValueError(f"No JSON object found in response: {text[:200]}...")
    
    text = match.group(0)
    
    # Remove invalid control characters
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # Try to fix common JSON issues
    text = text.replace("'", '"')
    text = text.replace("True", "true").replace("False", "false").replace("None", "null")
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}")
        logger.error(f"Text: {text[:500]}")
        # Try to extract first valid JSON object
        for i, line in enumerate(text.splitlines()):
            line = line.strip()
            if line.startswith('{') or line.startswith('['):
                try:
                    return json.loads(line)
                except:
                    continue
        raise ValueError(f"Could not parse JSON: {e}")

def Api_to_create(task):
    """Makes API call to generate code based on task and existing functions."""
    with OpenRouter(api_key=os.getenv("APIKEY")) as client:
        with open("functions.json", "r") as f:
            data = json.load(f)
        
        system_prompt = """
You are an expert Python software engineer.

Your job is to generate or update Python project files.

Rules:
1. Always return ONLY valid JSON.
2. Do not use markdown.
3. Do not use .
4. Do not include explanations or extra text.
5. Output must be parsable with json.loads().
6. Reuse existing files and functions whenever possible.
7. If functionality is similar, extend the existing file instead of creating a new one.
8. Organize reusable logic into helper functions when appropriate.
9. Never create duplicate functions.
10. If no new file/function is needed, return empty objects.

Required JSON format:
{
    "filename.py": "full python code here",
    "usecase": {
        "filename.py": {
            "function_name": "description and usage example"
        }
    }
}

The "usecase" object must describe:
- what the function does
- how to run it

Example:
{
    "math_utils.py": {
        "fibonacci": "Generates fibonacci numbers. Usage: fibonacci(n)"
    }
}

Only return raw JSON.
"""
        user_prompt = f"""
Task:
{task}

Existing functions and files:
{json.dumps(data, indent=4, default=str)}

Do not recreate existing functionality.
"""
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.send(
                    model="baidu/cobuddy:free",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                )
                break
            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise
        
        resp = safe_json_loads(response.choices[0].message.content)
        
        with open("api_response.json", "w") as f:
            json.dump({"response": resp}, f, indent=4)
        
        return resp

def make_new_function(task):
    """Creates or updates Python files based on API response."""
    logger.info("Making API call...")
    response = Api_to_create(task)
    
    if not response:
        logger.warning("Empty response received")
        return
    
    data = response
    logger.info("API call completed. Response received.")
    
    if data:
        # Handle case where response might be wrapped
        if "solution" in data:
            data = data["solution"]
        
        for name, code in data.items():
            if name == "usecase":
                continue
            file_name = name if name.endswith(".py") else name + ".py"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(code)
            logger.info(f"Created/updated: {file_name}")
        
        if "demo.py" in data:
            logger.info("Updating demo.py...")
            try:
                result = subprocess.run(["python", "demo.py"], check=True, capture_output=True, text=True)
                logger.info("demo.py executed successfully")
                if result.stdout:
                    logger.info(f"Output: {result.stdout[:500]}")
                shutil.copy("demo.py", "main.py")
            except subprocess.CalledProcessError as e:
                logger.error(f"demo.py execution failed: {e}")
                logger.error(f"Stderr: {e.stderr}")
                # Retry with reminder
                make_new_function(task + " reminder: last code had bugs")
    
    logger.info("Files created/updated based on API response.")
    
    if "usecase" in data:
        with open("functions.json", "r+", encoding="utf-8") as f:
            jsonfile = json.load(f)
            jsonfile.update(data["usecase"])
            f.seek(0)
            json.dump(jsonfile, f, indent=4)
            f.truncate()
        logger.info("Updated functions.json")

def think(thinkingtask):
    """Plans solution by asking model to think through the task."""
    with OpenRouter(api_key=os.getenv("APIKEY")) as client:
        response = client.chat.send(
            model="openai/gpt-oss-120b:free",
            messages=[
                {"role": "user", "content": "task: " + thinkingtask + '''
for this task you have to think whether we can do it with our current functions or make new function. Plan an entire pipeline.
You can give instructions or ask for present files. All functions are in functions.json. You can also ask for file contents.
Format should be JSON only, no text outside JSON.
If you have solution give: {"solution":"your solution"}
If you want to ask for files give: {"fetch":"filename","plan":"your plan"}
'''}
            ],
        )
        return response.choices[0].message.content

def fetch_file_content(filename):
    """Fetches content of a file."""
    try:
        with open(filename, "r") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return ""

def self_diagnose():
    """Self-diagnostic: checks own code quality and identifies improvements."""
    content = fetch_file_content("demo.py")
    issues = []
    
    if "except Exception:" in content and "as e" not in content:
        issues.append("Bare except clause without exception variable")
    
    if "print(" in content:
        issues.append("Using print() instead of logger")
    
    return {
        "status": "healthy" if not issues else "issues_found",
        "issues": issues,
        "content_length": len(content)
    }

def assistant(UserTask):
    """Orchestrates the entire workflow."""
    logger.info("Thinking...")
    response = think(UserTask)
    
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error(f"Could not parse think response: {response[:200]}")
        # Try safe_json_loads
        data = safe_json_loads(response)
    
    trigger = True
    logger.info("Thought process completed.")
    
    while trigger:
        if "solution" in data:
            logger.info("Executing solution...")
            make_new_function(data["solution"])
            trigger = False
        elif "fetch" in data:
            logger.info(f"Fetching content of {data['fetch']}...")
            content = fetch_file_content(data["fetch"])
            think(f"Original task: {UserTask}\nHere is the content of {data['fetch']}:\n{content}\nNow plan for the task: {UserTask}")

def self_improvement_entry():
    """Entry point for self-improvement cycle."""
    logger.info("Starting self-improvement cycle...")
    
    # Self-diagnose
    diag = self_diagnose()
    logger.info(f"Self-diagnosis: {json.dumps(diag, indent=2)}")
    
    if diag["status"] == "issues_found":
        make_new_function(f"Improve demo.py based on self-diagnosis: {json.dumps(diag)}")
    else:
        logger.info("No improvements needed.")

if __name__ == "__main__":
    self_improvement_entry()
