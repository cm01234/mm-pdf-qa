from pathlib import Path
import hashlib
import logging
from typing import Any

import pymupdf

from config import IMAGE_OUTPUT_DIR

logger = logging.getLogger(__name__)


class PDFProcessor:

    def __init__(
        self,
        pdf_path: str | Path,
        output_dir: str | Path = IMAGE_OUTPUT_DIR,
    ) -> None:

        self.pdf_path = Path(pdf_path)

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self) -> list[dict[str, Any]]:

        doc = pymupdf.open(self.pdf_path)

        documents = []

        for page_number, page in enumerate(doc, start=1):

            # =========================================
            # TEXT
            # =========================================

            text = page.get_text("text")

            if text.strip():

                documents.append(
                    {
                        "id": (f"text_" f"{page_number}"),
                        "type": "text",
                        "page": page_number,
                        "text": text.strip(),
                        "source": self.pdf_path.name,
                    }
                )

            # =========================================
            # TABLES
            # =========================================

            try:

                tables = page.find_tables()

                if tables:

                    for table_number, table in enumerate(tables.tables, start=1):

                        df = table.to_pandas()

                        table_text = df.to_string(index=False)

                        if table_text.strip():

                            documents.append(
                                {
                                    "id": (
                                        f"table_" f"{page_number}_" f"{table_number}"
                                    ),
                                    "type": "table",
                                    "page": page_number,
                                    "text": (
                                        "Table on page "
                                        f"{page_number}:\n\n"
                                        f"{table_text}"
                                    ),
                                    "source": (self.pdf_path.name),
                                }
                            )

            except Exception:
                logger.warning("Table extraction error", exc_info=True)

            # =========================================
            # IMAGES
            # =========================================

            images = page.get_images(full=True)

            seen = set()

            for image_number, image_info in enumerate(images, start=1):

                xref = image_info[0]

                if xref in seen:
                    continue

                seen.add(xref)

                try:

                    image = doc.extract_image(xref)

                    image_bytes = image["image"]

                    extension = image["ext"]

                    hash_value = hashlib.sha256(image_bytes).hexdigest()[:16]

                    filename = (
                        f"page_{page_number}_"
                        f"image_{image_number}_"
                        f"{hash_value}."
                        f"{extension}"
                    )

                    path = self.output_dir / filename

                    path.write_bytes(image_bytes)

                    documents.append(
                        {
                            "id": (f"image_" f"{page_number}_" f"{image_number}"),
                            "type": "image",
                            "page": page_number,
                            "image_path": str(path),
                            "text": (f"Image from page " f"{page_number}"),
                            "source": (self.pdf_path.name),
                        }
                    )

                except Exception:
                    logger.warning("Image extraction error", exc_info=True)

        doc.close()

        return documents
