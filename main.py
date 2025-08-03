import os
import json
from google import genai
from utils.loader import load_json_text
from utils.prompt_loader import load_prompt
import sys
import tty
import termios

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
chat = client.chats.create(model="gemini-2.0-flash")

def prompt_with_files(image_path=None, json_path=None, custom_note=None):
    parts = []

    if not parts:
        print("\n❗ No data provided. Please input text, upload an image or metrics file.\n")
        return

    if json_path:
        # run_data = load_json_text(json_path)
        run_data = load_json_text("assets/sample_run.json")
        formatted_prompt = load_prompt(
            "prompts/run_feedback.txt",
            run_data=json.dumps(run_data, indent=2),
            custom_note=custom_note or ""
        )
        parts.append(formatted_prompt)

    if image_path:
        uploaded_file = client.files.upload(file=image_path)

        formatted_prompt = load_prompt(
            "./prompts/run_feedback.txt",
            run_data=uploaded_file,
            custom_note=custom_note or ""
        )

        parts.append(formatted_prompt)
        parts.append(uploaded_file)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=parts
    )
    
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
    print("v1.1.0\n")

    while True:
        print("Press any key to start, or 'q' to quit: ", end='', flush=True)
        cmd = get_single_key().lower()
        print()  # Move to next line after keypress
        if cmd == "q":
            print("👋 Exiting. Have a great run!")
            break
        else:
            image_path = input("Image path (optional, e.g. /path/to/screenshot.jpg): ").strip()
            if image_path.lower() == 'q':
                print("👋 Exiting. Have a great run!")
                break
            json_path = input("Metrics file path (optional, e.g. assets/sample_run.json): ").strip()
            if json_path.lower() == 'q':
                print("👋 Exiting. Have a great run!")
                break
            note = input("Add any notes or goals (optional): ").strip()
            if note.lower() == 'q':
                print("👋 Exiting. Have a great run!")
                break

            prompt_with_files(
                image_path=image_path if image_path else None,
                json_path=json_path if json_path else None,
                custom_note=note if note else None
            )
            
            