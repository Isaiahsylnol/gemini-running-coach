def load_prompt(template_path: str, **kwargs) -> str:
    """
    Load a prompt template and format it with keyword arguments.

    Args:
        template_path (str): Path to the prompt file (e.g., prompts/run_feedback.txt).
        **kwargs: Variables to insert into the prompt.

    Returns:
        str: The formatted prompt ready to send to the LLM.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)