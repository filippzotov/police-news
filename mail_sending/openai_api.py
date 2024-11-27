import logging

from openai import OpenAI
import threading
from decouple import config


GPT_TOKEN = config("GPT_TOKEN")
# from decouple import config

logger = logging.getLogger(__name__)


# gpt-4o
# gpt-4-turbo-preview
def chatgpt_answer(prompt, model="gpt-4o"):
    result = {"response": None}

    def worker():
        client = OpenAI(
            # This is the default and can be omitted
            api_key=GPT_TOKEN,
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
        )
        result["response"] = chat_completion.choices[0].message.content
        result["tokens"] = chat_completion.usage

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=500)  # Set the timeout to 10 seconds

    if thread.is_alive():
        print("The request timed out!")
        # thread.join()  # Optionally join the thread even if it times out
        return None
    return result


if __name__ == "__main__":
    prompt = "What is the capital of France?"
    response = chatgpt_answer(prompt)
    print(response)
