"""
Sift Gemini provider.

Reuses the existing ai/gemini.py configuration so the
project has one Gemini client and one model configuration.
"""

from ai import gemini


class GeminiProvider:
    """
    Adapter around the existing ai.gemini module.

    ai/gemini.py is responsible for:

        - loading .env
        - reading GEMINI_API_KEY
        - creating the Gemini client
        - selecting the model
        - sending prompts to Gemini
    """

    def __init__(self):
        self.model_name = gemini.MODEL

    def generate(self, prompt):
        """
        Generate plain text using the existing Gemini
        implementation.
        """

        if not prompt or not str(prompt).strip():
            raise ValueError(
                "GeminiProvider.generate() "
                "received an empty prompt."
            )

        response = gemini.generate(
            str(prompt)
        )

        if not response:
            raise RuntimeError(
                "Gemini returned empty text."
            )

        return response.strip()