## File Organizer

An LLM-powered file organizer that organizes your files on disk.

### Instructions

The default model used by the app is `gemini/gemini-2.5-flash`, so before running export the `GEMINI_API_KEY` environment variable, then run the app using [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
uvx --from git+https://github.com/deyarchit/file-organizer organizer <path_to_organize>
```

*Note: The tool performs file moves directly in the original directory. During plan evaluation, it detects and reports any files that were added or removed.*

### Demo

[![asciicast](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU.png)](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU)
