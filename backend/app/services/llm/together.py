from __future__ import annotations

from typing import Optional

import httpx


class TogetherClient:
    """Minimal wrapper around Together.ai chat completions API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.together.xyz/v1",
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.2,
        max_output_tokens: int = 600,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("Together API key must be provided.")

        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.post(
            "/chat/completions",
            json={
                "model": self._model,
                "temperature": self._temperature,
                "max_output_tokens": self._max_output_tokens,
                "messages": messages,
            },
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("Together API returned no choices.")
        return choices[0]["message"]["content"].strip()

    def close(self) -> None:
        self._client.close()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:  # noqa: BLE001
            pass
