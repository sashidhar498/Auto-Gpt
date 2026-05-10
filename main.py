
import json
import os
from dotenv import load_dotenv
load_dotenv()
import subprocess

from openrouter import OpenRouter
import os
def Api_to_create(task):
    with OpenRouter(api_key=os.getenv("APIKEY")) as client:
        system_prompt = """
You are an expert Python software engineer.

Your job is to generate or update Python project files.

Rules:
1. Always return ONLY valid JSON.
2. Do not use markdown.
3. Do not use ```json.
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
        with open("functions.json", "r") as f:
            data = json.load(f)
        user_prompt = f"""
Task:
{task}

Existing functions and files:
{json.dumps(data, indent=4)}

Do not recreate existing functionality.
"""
        response = client.chat.send(
            model="inclusionai/ring-2.6-1t:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )
        resp=response.choices[0].message.content.replace("```json", "")
        resp=resp.replace("```", "")
        with open("api_response.json", "w") as f:
            json.dump({"response": resp}, f, indent=4)

        return resp

def make_new_function(task):
    print("Making API call...")
    response = Api_to_create(task)
    # print(response)
    data=json.loads(response)
    print("API call completed. Response:",response[:50])
    if data:
        name= list(data.keys())[0]
        file_name = name if ".py" in name else name + ".py"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(data[name])
        if file_name=="demo.py":
            print("Updating demo.py...")
            working=subprocess.run(["python", "demo.py"], check=True)
            if not working:
                make_new_function(task+ "reminder: last code had bugs")


    print("Files created/updated based on API response.")
    if data["usecase"]:
        with open("functions.json", "r+", encoding="utf-8") as f:
            jsonfile = json.load(f)
            # print(data)
            # print(response)
            jsonfile.update(data["usecase"])
            # print(data)
            f.seek(0)
            json.dump(jsonfile, f,indent=4)

def think(thinkingtask):
     with OpenRouter(api_key=os.getenv("APIKEY")) as client:
        response = client.chat.send(
            model="openai/gpt-oss-120b:free",
            messages=[
                {"role": "user", "content": "task: "+thinkingtask + ''' for this task you have to thik weather we can do it with out current functions or make new function we need to plan an entire pipeline. you can give instruction or ask for present files, all the functions are in functions.json file and you can also ask for the content of the files if you want. format should be json and only json no text outside of json and no random symbols just json response like if you have solution give output as just {\"solution\":\"your solution\"} else if you want to ask for files or content of files give output as {\"fetch\":\"filename\",\"plan\":\"your plan for this task\"}
                in solution you have to give everything perfectly
'''}
            ],
        )

        return response.choices[0].message.content
def fetch_file_content(filename):
    with open(filename, "r") as f:
        content = f.read()
    return content

def assistant(UserTask):
    print("Thinking...")
    response = think(UserTask)
    data=json.loads(response)
    trigger=True
    print("Thought process completed. Response:",response[:50])
    while trigger:
        if "solution" in data:
            print("Executing solution...")
            make_new_function(data["solution"])
            trigger=False
        elif "fetch" in data:
            print(f"Fetching content of {data['fetch']} for further planning...")
            content = fetch_file_content(data["fetch"])
            think(f"Original task: {UserTask}\nHere is the content of {data['fetch']}:\n{content}\n Now plan for the task: {UserTask}")
        
make_new_function("i want you to understand yourself, i made you , you are an ai in my autogen project demo.py you conents are"+str(fetch_file_content("demo.py"))+"try to make yourself better")