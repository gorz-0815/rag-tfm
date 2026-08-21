from src.prompts import NO_CONTEXT_MESSAGE, build_context_prompt, load_system_prompt


def test_no_context_message_is_non_empty():
    assert NO_CONTEXT_MESSAGE


def test_load_system_prompt_is_non_empty():
    assert load_system_prompt()


def test_build_context_prompt_includes_question_and_context():
    prompt = build_context_prompt("How do I clean it?", "Unplug before cleaning.")

    assert "How do I clean it?" in prompt
    assert "Unplug before cleaning." in prompt
