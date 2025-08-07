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

def prompt_with_files(image_path=None, json_path=None, custom_note=None):
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
        print("\n❗ No data provided. Please input text, upload an image or metrics file.\n")
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
            print("Press any key to start a new entry, or 'q' to quit: ", end='', flush=True)
            cmd = get_single_key().lower()
            print()  # Move to next line after keypress
            if cmd == "q":
                break
            else:
                image_path = input("Image path (optional, e.g. /path/to/screenshot.jpg): ").strip()
                if image_path.lower() == 'q':
                    break
                json_path = input("Metrics file path (optional, e.g. assets/sample_run.json): ").strip()
                if json_path.lower() == 'q':
                    break
                note = input("Add any notes or goals (optional): ").strip()
                if note.lower() == 'q':
                    break

                prompt_with_files(
                    image_path=image_path if image_path else None,
                    json_path=json_path if json_path else None,
                    custom_note=note if note else None
                )
    finally:
        save_chat_history(chat_history)
        print("👋 Exiting. Have a great run!")
