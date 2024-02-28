#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

import socket
from openai import AzureOpenAI
import re

import requests

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation.
When showing HTML, always include what is in the body tag, 
but exclude the code surrounding the actual content. 
So exclude always BODY, HEAD and HTML .
"""

MODEL = "gpt-35-turbo"
AI = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


"""
import re
from pathlib import Path
text = Path("util/test/chess.txt").read_text()
text = Path("util/test/html.txt").read_text()
text = Path("util/test/code.txt").read_text()
"""
def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
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
    return res

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")

    if(is_valid_email_format(input)):
        send_message_to_slack(input)
        email_status = get_email_status(input);
        res = {
                "output": "Hai inserito la e-mail "+input+". Risposta da Bouncer: " + email_status,
                "title": "Gestione E-Mail",
                "message": "Risposta da Bouncer: " + email_status
            }
    elif input == "":
        res = {
            "output": "Welcome to the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        input = get_url_prompt_prefix(input) + input
        output = ask(input)
        res = extract(output)
        res['output'] = output

    return {"body": res }

def get_email_status(email):
    response = call_bouncer(email)

    if(response.status_code == 200):
        if(response.score > 0): return "La mail esiste"
        else: return "La mail non esiste"
    elif(response.status_code == 402): 
        return "Pagamento richiesto"
    elif(response.status_code == 403): 
        return "Troppe richieste"
    else: return "Errore generico"


def call_bouncer(email):
    api_key = "qualcosa"
    url = f"https://api.usebouncer.com/v1.1/email/verify"
    params = {"email": email}
    headers = {"x-api-key": f"{api_key}"}
    return requests.get(url, params=params, headers=headers)



def is_valid_email_format(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        return False

def send_message_to_slack(text):
    url = "https://nuvolaris.dev/api/v1/web/utils/demo/slack"
    params = {"text": text}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("Messaggio inviato a slack: "+ text)
    else:
        print(f"Si è verificato un errore {response}")
    
def get_url_prompt_prefix(string):
    prompt_prefix=""
    url_pattern = r"(?i)\b(?:https?://)?(?:www\.\w+\.[a-z]{2,4}(?:\.[a-z]{2})?|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\b[a-z0-9.\-]+\.[a-z]{2,4}(?:\.[a-z]{2})?)(?:\:\d+)?(?:[/?]\S*)?\b"
    urls = re.findall(url_pattern, string)

    if(len(urls)>0):
        prompt_prefix="Assuming "
        for url in urls: 
            prompt_prefix += " " + url + " has IP address " + get_ip_from_url(url) + ", "
        prompt_prefix+=" answer to this question: "
        send_message_to_slack("[RISOLUZIONE INDIRIZZO IP] "+prompt_prefix+" "+string)

    return prompt_prefix

def get_ip_from_url(url):
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]
    if "/" in url:
        url = url.split("/")[0]
    try:
        ip_address = socket.gethostbyname(url)
        return ip_address
    except socket.gaierror:
        print("Impossibile risolvere l'indirizzo IP.")
        return "NONE"