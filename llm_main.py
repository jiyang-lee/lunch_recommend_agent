"""Compatibility wrapper for the CLI entry point."""

from llm.llm_main import main


if __name__ == "__main__":
    raise SystemExit(main())
