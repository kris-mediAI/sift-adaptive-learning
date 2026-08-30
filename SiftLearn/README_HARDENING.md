# Sift Backend Hardening

## How to install

Back up your current project first.

Then copy the files in this bundle over the corresponding files in your Sift project.

Do **not** copy the UI directory from this bundle because there isn't one.

## Environment

Existing environment variables remain valid.

Optional Gemini reliability settings:

```text
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_MAX_RETRIES=2
GEMINI_RETRY_BACKOFF=1.0
```

Do not put API keys in source files.

## Offline verification

From the project root:

```powershell
python verify_backend_hardening.py
```

This performs local checks without making Gemini or YouTube requests.

Then run your existing test suite in the project's `.venv`.

## Important

This bundle is a hardening pass, not a replacement architecture. It preserves the supplied Sift components and their public flow wherever possible.
