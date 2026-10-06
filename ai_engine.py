import os
import base64
import json
import urllib.request
import urllib.error


# ============================================================
# TrailTalk - Local Ollama AI Engine
# ============================================================
#
# This module intentionally DOES NOT contain a fake species
# identification fallback.
#
# If Ollama/Gemma is unavailable, TrailTalk reports the failure
# instead of inventing an identification.
#
# ============================================================


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
REQUIRED_MODEL = "gemma3:4b"


OLLAMA_API_URL = os.environ.get(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
).rstrip("/")


def _candidate_urls():
    """
    Return possible local Ollama URLs.

    This helps when localhost resolves differently on macOS.
    """
    urls = [
        OLLAMA_API_URL,
        "http://127.0.0.1:11434",
        "http://localhost:11434",
    ]

    result = []
    seen = set()

    for url in urls:
        if url and url not in seen:
            result.append(url)
            seen.add(url)

    return result


def _get_ollama_tags(url):
    """
    Query Ollama's model list.

    Uses requests when available, otherwise urllib.
    Returns:
        list[str]
    """

    endpoint = f"{url}/api/tags"

    # --------------------------------------------------------
    # Try requests first
    # --------------------------------------------------------
    try:
        import requests

        response = requests.get(
            endpoint,
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()

            return [
                model.get("name")
                for model in data.get("models", [])
                if model.get("name")
            ]

    except Exception:
        pass

    # --------------------------------------------------------
    # Standard-library fallback
    # --------------------------------------------------------
    try:
        request = urllib.request.Request(
            endpoint,
            headers={
                "User-Agent": "TrailTalk/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=3
        ) as response:

            if response.status == 200:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)

                return [
                    model.get("name")
                    for model in data.get("models", [])
                    if model.get("name")
                ]

    except Exception:
        pass

    return None


def check_ollama_status():
    """
    Check whether the local Ollama server is available.

    Returns exactly three values because app.py expects:

        ollama_ready, available_models, active_url

    Example:

        (
            True,
            ["gemma3:4b", "llama3.2:latest"],
            "http://127.0.0.1:11434"
        )
    """

    for url in _candidate_urls():

        models = _get_ollama_tags(url)

        if models is not None:
            return True, models, url

    return False, [], OLLAMA_API_URL


def encode_image_to_base64(image_bytes):
    """
    Convert image bytes to a base64 string suitable for Ollama.
    """

    return base64.b64encode(image_bytes).decode("utf-8")


def _build_system_prompt():
    """
    Prompt used for nature identification.

    The model is explicitly instructed not to claim certainty
    when the photograph does not support species-level
    identification.
    """

    return """
You are TrailTalk AI, a local ecological field guide.

You are analyzing a photograph taken during an outdoor walk.

Analyze ONLY what is visually supported by the photograph.

Return ONLY valid JSON.

Use exactly these keys:

{
    "species_name": "Common name, with scientific name if reasonably identifiable",
    "category": "Plant | Bird | Tree | Insect | Fungi | Other",
    "confidence": "High | Medium | Low",
    "fun_fact": "One useful ecological or biological fact.",
    "identification_traits": "Visible physical traits that support the identification.",
    "care_or_safety_note": "Relevant safety, toxicity, invasiveness, protection, or observation guidance."
}

Important rules:

1. Do NOT invent an identification.
2. Do NOT claim High confidence unless the image provides strong evidence.
3. If exact species identification is not possible, say so.
4. Do not infer a species solely from the user's hint.
5. Base the identification on visible evidence.
6. If the image is unclear, use Low confidence.
7. The output must be valid JSON with no markdown fences.
"""


def _make_payload(
    image_bytes,
    user_hint,
    model
):
    """
    Construct the Ollama /api/generate request.
    """

    image_base64 = encode_image_to_base64(image_bytes)

    hint = (
        user_hint.strip()
        if user_hint and user_hint.strip()
        else "Identify what is visible in this nature photograph."
    )

    prompt = (
        _build_system_prompt()
        + "\n\nUser context hint:\n"
        + hint
    )

    return {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "format": "json",
    }


def _post_to_ollama(
    url,
    payload
):
    """
    Send an inference request to Ollama.

    Returns the raw response text or raises an exception.
    """

    endpoint = f"{url}/api/generate"

    # --------------------------------------------------------
    # Try requests
    # --------------------------------------------------------
    try:
        import requests

        response = requests.post(
            endpoint,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data.get("response", "")

    except ImportError:
        pass

    except Exception as requests_error:
        # Try urllib below before giving up.
        last_error = requests_error
    else:
        last_error = None

    # --------------------------------------------------------
    # Standard-library implementation
    # --------------------------------------------------------
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "TrailTalk/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            raw = response.read().decode("utf-8")
            data = json.loads(raw)

            return data.get("response", "")

    except Exception as urllib_error:

        if last_error is not None:
            raise RuntimeError(
                f"Ollama request failed: {last_error}; "
                f"urllib fallback failed: {urllib_error}"
            )

        raise RuntimeError(
            f"Ollama request failed: {urllib_error}"
        )


def _failure_result(message):
    """
    Return an explicit failure result.

    IMPORTANT:
    This is NOT a species identification.
    """

    return {
        "success": False,
        "demo_mode": True,
        "error": message,
        "ai_model_used": None,

        "species_name": "No identification",
        "category": "Unknown",
        "confidence": "Low",

        "fun_fact": "",
        "identification_traits": "",
        "care_or_safety_note": "",
    }


def identify_nature_element(
    image_bytes,
    user_hint="",
    preferred_model=REQUIRED_MODEL
):
    """
    Identify a nature subject using local Ollama vision AI.

    There is deliberately NO fake identification fallback.

    Successful result:

        success = True
        demo_mode = False
        ai_model_used = "Local Ollama (gemma3:4b)"

    Failed result:

        success = False
        demo_mode = True
        species_name = "No identification"
    """

    # --------------------------------------------------------
    # Validate image
    # --------------------------------------------------------

    if not image_bytes:
        return _failure_result(
            "No image was provided."
        )

    # --------------------------------------------------------
    # Check Ollama
    # --------------------------------------------------------

    is_online, available_models, active_url = check_ollama_status()

    if not is_online:
        return _failure_result(
            "Ollama is not running. "
            "Start Ollama with 'ollama serve' and try again."
        )

    # --------------------------------------------------------
    # Require the intended vision model.
    #
    # We deliberately DO NOT silently switch to another model.
    # This makes the demo reproducible and honest.
    # --------------------------------------------------------

    if preferred_model not in available_models:

        available = (
            ", ".join(available_models)
            if available_models
            else "none"
        )

        return _failure_result(
            f"Required vision model '{preferred_model}' "
            f"is not installed. Available models: {available}"
        )

    # --------------------------------------------------------
    # Build request
    # --------------------------------------------------------

    payload = _make_payload(
        image_bytes=image_bytes,
        user_hint=user_hint,
        model=preferred_model,
    )

    # --------------------------------------------------------
    # Run real local inference
    # --------------------------------------------------------

    try:

        result_text = _post_to_ollama(
            active_url,
            payload
        )

        if not result_text:
            return _failure_result(
                "Ollama returned an empty response."
            )

        # ----------------------------------------------------
        # Parse JSON returned by Gemma
        # ----------------------------------------------------

        try:
            parsed = json.loads(result_text)

        except json.JSONDecodeError as json_error:

            return _failure_result(
                "Gemma returned invalid JSON. "
                f"Raw response could not be parsed: {json_error}"
            )

        # ----------------------------------------------------
        # Validate expected fields
        # ----------------------------------------------------

        required_fields = [
            "species_name",
            "category",
            "confidence",
            "fun_fact",
            "identification_traits",
            "care_or_safety_note",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in parsed
        ]

        if missing_fields:

            return _failure_result(
                "Gemma returned an incomplete response. "
                f"Missing fields: {', '.join(missing_fields)}"
            )

        # ----------------------------------------------------
        # Mark this as a REAL model result
        # ----------------------------------------------------

        parsed["success"] = True
        parsed["demo_mode"] = False
        parsed["ai_model_used"] = (
            f"Local Ollama ({preferred_model})"
        )

        # Keep track of the actual endpoint used.
        parsed["ollama_url"] = active_url

        return parsed

    except Exception as error:

        print(
            f"TrailTalk Ollama inference error: {error}"
        )

        return _failure_result(
            "Ollama inference failed. "
            "No identification was generated."
        )


def generate_trail_summary(sightings_list):
    """
    Generate a summary of the user's logged outdoor sightings.

    This is a local deterministic summary. It does not pretend
    that an additional AI model generated the recap.
    """

    if not sightings_list:
        return (
            "🌲 **Trail Walk Summary**\n\n"
            "No sightings logged on this trail yet. "
            "Get outside, take a photo, and start exploring!"
        )

    total_count = len(sightings_list)

    categories = {}
    unique_species = set()

    for sighting in sightings_list:

        category = sighting.get(
            "category",
            "Other"
        )

        categories[category] = (
            categories.get(category, 0) + 1
        )

        species = sighting.get(
            "species_name",
            "Unknown"
        )

        unique_species.add(species)

    species_sample = ", ".join(
        list(unique_species)[:5]
    )

    recap = (
        f"🌲 **Trail Walk Summary**\n\n"
        f"You logged **{total_count} observation(s)** "
        f"across species such as "
        f"**{species_sample}**.\n\n"
    )

    recap += "**Breakdown by category:**\n"

    for category, count in categories.items():
        recap += (
            f"- **{category}**: {count}\n"
        )

    recap += (
        "\n✨ **Local AI:** "
        "Nature identifications were generated using "
        "the local Ollama vision model when available. "
        "No identification is fabricated when the model "
        "is unavailable."
    )

    return recap
