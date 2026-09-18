import os
import base64
from pathlib import Path

import ollama
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")


def ask_llm(prompt):
    """
    Ask the local Qwen model a text-only question.
    """

    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"]


def image_to_base64(image_path):
    """
    Convert image to base64.
    """

    data = Path(image_path).read_bytes()

    return base64.b64encode(data).decode("utf-8")


def analyze_image(image_path, page_number):

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

    response = ollama.chat(
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
