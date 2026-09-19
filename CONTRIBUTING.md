# Contributing

This project was made for fun and experimentation. It must not be used in real
case scenarios, production workflows, or decisions that affect people.

This repository intentionally does not include a license file.

## Before Opening a Pull Request

- Keep changes focused and explain the user-facing behavior.
- Run `ruff check` on the Python source.
- Run `PYTHONPATH=. venv/bin/python -m pytest -q`.
- Run `pip-audit -r requirements.txt` when `pip-audit` is available.
- Do not commit PDFs, generated ChromaDB data, extracted images, `.env` files,
  model weights, or other private data.

## Pull Requests

Describe the problem, the approach taken, and the validation performed. Include
tests for behavior changes where practical. Contributions may be declined if
they conflict with the project's experimental scope or safety disclaimer.
