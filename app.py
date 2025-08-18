import gradio as gr

def evaluate_run(image, json_file, notes):
    # Process inputs and pass to Gemini (mocked response here)
    return f"Processed {image.name if image else 'no image'} + {json_file.name if json_file else 'no json'} + notes: {notes}"

demo = gr.Interface(
    fn=evaluate_run,
    inputs=[
        gr.Image(type="filepath", label="Upload Run Screenshot (optional)"),
        gr.File(file_types=[".json", ".txt"], label="Upload Run Data File"),
        gr.Textbox(label="Any Notes?")
    ],
    outputs="text",
    title="Running Coach AI",
    description="Upload your session data or screenshot and get AI fitness advice."
)

demo.launch()