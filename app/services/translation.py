import json
import time
from openai import OpenAI
from flask import current_app
from app.utils.caching import cache_result

client = OpenAI()

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


@cache_result(expire_seconds=86400)  # Cache for 24 hours
def translate_to_korean(text):
    """Translates English text to Korean using OpenAI with structured output."""
    if not text or len(text.strip()) == 0:
        raise ValueError("Empty text provided for translation")

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful translator. Translate the given English text to Korean. Respond with a JSON object containing a single key 'korean_translation' with the translated text as the value.",
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=150,
            )

            response_content = response.choices[0].message.content
            translation_data = json.loads(response_content)
            translation = translation_data.get("korean_translation")

            if not translation:
                current_app.logger.error(
                    f"Translation missing from response: {response_content}"
                )
                raise ValueError("Translation missing from API response")

            return translation

        except json.JSONDecodeError as e:
            current_app.logger.error(
                f"JSON decode error: {e}, Response: {response_content if 'response_content' in locals() else 'N/A'}"
            )
            if attempt == MAX_RETRIES - 1:
                raise
        except Exception as e:
            current_app.logger.error(
                f"Translation error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)

    raise RuntimeError("Failed to translate after maximum retries")


def generate_conversation_scenario(prompt, min_lines=2, max_lines=4):
    """
    Generate a short conversation scenario (2-4 lines) using OpenAI, returning structured JSON with title, description, and lines.
    Each line includes: speaker (1 or 2), english_text, korean_text.
    """
    if not prompt or len(prompt.strip()) == 0:
        raise ValueError("Empty prompt provided for conversation generation")

    system_prompt = (
        "You are a helpful assistant for language learners. "
        "Given a scenario prompt, generate a short, realistic conversation in English and Korean between two speakers. "
        f"The conversation should have between {min_lines} and {max_lines} lines. "
        "Return a JSON object with the following structure: "
        "{ 'title': <title>, 'description': <description>, 'lines': [ { 'speaker': 1 or 2, 'english_text': <text>, 'korean_text': <text> }, ... ] } "
        "Speakers should alternate. Keep lines concise and natural."
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=600,
            )
            response_content = response.choices[0].message.content
            current_app.logger.info(f"OpenAI raw response: {response_content!r}")
            scenario_data = json.loads(response_content)
            # Basic validation
            if not scenario_data.get("lines") or not isinstance(
                scenario_data["lines"], list
            ):
                raise ValueError("No lines found in conversation response")
            return scenario_data
        except json.JSONDecodeError as e:
            current_app.logger.error(
                f"JSON decode error: {e}, Response: {response_content if 'response_content' in locals() else 'N/A'}"
            )
            if attempt == MAX_RETRIES - 1:
                raise
        except Exception as e:
            current_app.logger.error(
                f"Conversation generation error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Failed to generate conversation after maximum retries")
