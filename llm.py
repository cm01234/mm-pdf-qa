import os
import base64
from pathlib import Path
from typing import Any

import ollama
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:4b")


class OllamaConfigurationError(RuntimeError):
    """Raised when Ollama is unavailable or the configured model is missing."""


def chat_with_ollama(**kwargs: Any) -> Any:
    try:
        return ollama.chat(**kwargs)
    except ollama.ResponseError as error:
        if error.status_code == 404 or "not found" in str(error).lower():
            raise OllamaConfigurationError(
                f"Ollama model '{MODEL}' is not installed. "
                f"Run `ollama pull {MODEL}` and try again."
            ) from error

        raise OllamaConfigurationError(
            f"Ollama returned an error: {error}"
        ) from error
    except Exception as error:
        message = str(error).lower()
        connection_errors = (
            "connection refused",
            "failed to connect",
            "connection error",
            "cannot connect",
            "all connection attempts failed",
            "connection reset",
            "network is unreachable",
            "timed out",
            "timeout",
        )

        if any(item in message for item in connection_errors):
            raise OllamaConfigurationError(
                "Ollama is not running. Start it with `ollama serve` and try again."
            ) from error

        raise


def ask_llm(prompt: str) -> str:
    """
    Ask the local Qwen model a text-only question.
    """

    response = chat_with_ollama(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]


def image_to_base64(image_path: str | os.PathLike[str]) -> str:
    """
    Convert image to base64.
    """

    data = Path(image_path).read_bytes()

    return base64.b64encode(data).decode("utf-8")


def analyze_image(image_path: str | os.PathLike[str], page_number: int) -> str:

    image_base64 = image_to_base64(
        image_path
    )

    prompt = f"""
Analyze this image from PDF page {page_number}.

Extract information useful for answering questions
about the PDF.

If it is a chart:
- identify the title
- axes
- legend
- categories
- values
- percentages
- trends
- highest and lowest values

If it is a table:
- extract the important rows, columns and values

If it is a diagram:
- explain the important components and relationships

If it is an image:
- describe relevant information

Do not invent information.
Return a concise factual description.
"""

    response = chat_with_ollama(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_base64]
            }
        ],
        options={
            "num_ctx": 6144
        }
    )

    return response["message"]["content"]
