from openai import OpenAI
import re

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation,
show it always as a markdown code block with the prefix "FEN:" in uppercase.
When requested to show HTML always include what is in the body tag, 
but exclude the boilerplate code surrounding the body tag.
"""

MODEL = "gpt-3.5-turbo"
AI = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        return comp.choices[0].message.content
    return "ERROR"


"""
import re
from pathlib import Path
text = Path("util/chess.txt").read_text()
text = Path("util/html.txt").read_text()
text = Path("util/code.txt").read_text()
text
"""
def extract(text):
    res = {}
    # search for languages
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    # search for a chess position
    pattern = r"FEN: (.*?)\n"
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    if len(m) > 0:
        res['chess'] = m[0]
        return res
    return res


def main(args):
    global AI
    AI = OpenAI(api_key=args.get("OPENAI_API_KEY"))

    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Welcome to the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        output = ask(input)
        res = extract(output)
        res['output'] = output

    return {"body": res }
