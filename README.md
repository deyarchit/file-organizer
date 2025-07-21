## File Organizer

An LLM-powered file organizer that organizes your files on disk.

### Instructions

This app currently supports only Gemini. Export the `GEMINI_API_KEY` environment variable, then run the app using `uv run main.py`.

```bash
uv run main.py <path_to_organize>
```

*Note: The tool performs file moves directly in the original directory. During plan evaluation, it detects and reports any files that were added or removed.*

### Demo

[![asciicast](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU.png)](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU)
