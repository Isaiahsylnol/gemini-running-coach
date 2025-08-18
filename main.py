import os
import json
from google import genai
from utils.loader import load_json_text
from utils.prompt_loader import load_prompt
import sys
import tty
import termios

chat_history = []

def save_chat_history(history, filename="chat_history.json"):
    """Saves the chat history to a JSON file."""
    with open(filename, "w") as f:
        serializable_history = []
        for content in history:
            role = content.get("role")
            parts = content.get("parts", [])
            serializable_parts = []
            for part in parts:
                text = part.get("text")
                if text is not None:
                    serializable_parts.append(text)
                else:
                    serializable_parts.append("[NON-TEXT PART]")
            serializable_history.append({
                "role": role,
                "parts": serializable_parts
            })
        json.dump(serializable_history, f, indent=4)

def load_chat_history(filename="chat_history.json"):
    """Loads the chat history from a JSON file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                raw_history = json.load(f)
                return [
                    {
                        "role": item["role"],
                        "parts": [{"text": part} for part in item["parts"]]
                    }
                    for item in raw_history
                ]
            except json.JSONDecodeError:
                return []
    return []

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Load previous chat history if it exists
chat_history = load_chat_history()
chat = client.chats.create(model="gemini-1.5-flash", history=chat_history)

def prompt_with_text(text):
    if not text.strip():
        print("\n❗ No text provided. Please input some text.\n")
        return
    # run_data = load_json_text("assets/sample_run.json")
    run_data = None
    formatted_prompt = load_prompt(
            "prompts/run_feedback.txt",
            run_data=json.dumps(run_data, indent=2),
            custom_note=text.strip() or ""
        )

    chat_history.append({
        "role": "user",
        "parts": [{"text": text}]
    })

    # Send to Gemini and get response
    response = chat.send_message(formatted_prompt)

    chat_history.append({
        "role": "model",
        "parts": [{"text": response.text}]
    })
    print(f"\n🧠 Coach Says:\n{response.text}\n")

def file_prompt_with_text(text, file_path):
    """Sends a text prompt with a file to the Gemini model."""
    if not text.strip():
        print("\nNo text provided. Please input some text.\n")
        return

    if not file_path:
        print("\nNo file path provided. Please input a valid file path.\n")
        return

    if not os.path.exists(file_path):
        print(f"\nFile not found: {file_path}\n")
        return

    run_data = load_json_text(file_path)
    formatted_prompt = load_prompt(
        "prompts/run_feedback.txt",
        run_data=json.dumps(run_data, indent=2),
        custom_note=text.strip() or ""
    )

    chat_history.append({
        "role": "user",
        "parts": [{"text": text}, {"text": "[FILE]"}]
    })

    # Send to Gemini and get response
    response = chat.send_message(formatted_prompt)

    chat_history.append({
        "role": "model",
        "parts": [{"text": response.text}]
    })
    print(f"\n🧠 Coach Says:\n{response.text}\n")
    
def prompt_with_image(image_path=None, json_path=None, custom_note=None):
    parts = []

    if json_path:
        run_data = load_json_text("assets/sample_run.json")
        formatted_prompt = load_prompt(
            "prompts/run_feedback.txt",
            run_data=json.dumps(run_data, indent=2),
            custom_note=custom_note or ""
        )
        parts.append(formatted_prompt)

    if image_path:
        uploaded_file = client.files.upload(file=image_path)
        parts.append(uploaded_file)
        if not custom_note and not json_path:
            parts.insert(0, "Analyze this image.")

    if custom_note:
        parts.append(custom_note)

    if not parts:
        print("\nNo data provided. Please input text, upload an image or metrics file.\n")
        return

    chat_history.append({
        "role": "user",
        "parts": [{"text": p} if isinstance(p, str) else {"text": "[FILE]"} for p in parts]
    })

    # Send to Gemini and get response
    response = chat.send_message(parts)

    chat_history.append({
        "role": "model",
        "parts": [{"text": response.text}]
    })
    print(f"\n🧠 Coach Says:\n{response.text}\n")

def prompt_with_files_and_text(text, json_path=None):
    """Sends a text prompt with optional JSON file to the Gemini model."""
    if not text.strip():
        print("\nNo text provided. Please input some text.\n")
        return

    # Add running coach context
    context = (
        "You are a knowledgeable, supportive running coach. "
        "Give concise, actionable, and encouraging advice to runners of all levels. "
        "Always respond as a running coach.\n"
    )

    parts = [context + text.strip()]

    if json_path:
        if not os.path.exists(json_path):
            print(f"\nJSON file not found: {json_path}\n")
            return
        run_data = load_json_text(json_path)

        json_text = f"\nHere is the user's run data:\n{json.dumps(run_data, indent=2)}"
        parts.append(json_text)

    chat_history.append({
        "role": "user",
        "parts": [{"text": p} if isinstance(p, str) else {"text": "[FILE]"} for p in parts]
    })

    # Send to Gemini and get response
    response = chat.send_message(parts)

    chat_history.append({
        "role": "model",
        "parts": [{"text": response.text}]
    })
    print(f"\n🧠 Coach Says:\n{response.text}\n")

def get_single_key():
    """Wait for a single keypress and return it."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

if __name__ == "__main__":
    print("\n🏃‍♂️ Welcome to the Lite Running Coach!")
    print("You can upload a screenshot and/or a metrics file of your running workouts for feedback.")
    print("v1.2.0\n")

    try:
        while True:
            print("Press any key to start a new entry, or 'q' to quit: \n 't' - text prompt \n 'i' - image prompt \n 'f' - file prompt", end='', flush=True)
            cmd = get_single_key().lower()
            print()  # Move to next line after keypress
            if cmd == "q":
                break
            elif cmd == "t":
                print("\n✍️ Enter your text prompt (type 'q' to quit):")
                user_input = input("Prompt: ").strip()
                if user_input.lower() == 'q':
                    break
                prompt_with_text(user_input)
            elif cmd == "i":
                print("\n✍️ Enter your image prompt (type 'q' to quit):")
                user_input = input("Prompt: ").strip()
                if user_input.lower() == 'q':
                    break
                prompt_with_image(user_input)
            elif cmd == "f":
                print("\n✍️ Enter your file prompt (type 'q' to quit):")
                user_input = input("Prompt: ").strip()
                if user_input.lower() == 'q':
                    break
                text = input("file path: ").strip()
                file_prompt_with_text(
                    user_input,
                    text if text else None)

    finally:
        save_chat_history(chat_history)
        print("👋 Exiting. Have a great run!")
