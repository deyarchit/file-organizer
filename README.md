## File Organizer

A LLM powered file organizer to organize your files on disk.

### Instructions

This app currently only supports gemini, so export `GEMINI_API_KEY` to terminal and the run the app using `uv run main.py`.

```
uv run main.py <path_to_organize>
```

*Note: This will directly make the file moves in the orginal directory. As part of the plan evaluation the app checks if any files were removed/added, if that is the case then the app will report that.*

### Demo

[![asciicast](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU.png)](https://asciinema.org/a/rdrltLO80IGb8NXgbu8cLQCjU)
