# Copyright (c) 2025 CodeLibs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Ollama LLM client implementation.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from pydantic import ValidationError

from .base import ComposeOutput, IntentOutput
from .prompts import (
    COMPOSE_SYSTEM_PROMPT,
    COMPOSE_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama LLM client for intent extraction and answer composition.
    """

    def __init__(
        self,
        base_url: str,
        model: str = "gpt-oss",
        timeout_ms: int = 3000,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_ms = timeout_ms
        self.temperature = temperature
        self.top_p = top_p
        self.client = httpx.AsyncClient(timeout=timeout_ms / 1000.0)

    async def intent(
        self,
        query: str,
        system_prompt: str,
        user_template: str,
        language: str | None = None,
        filters: dict[str, Any] | None = None,
        query_history: list[str] | None = None,
        timeout_ms: int | None = None,
    ) -> IntentOutput:
        """
        Extract search intent from user query with optional query history context.
        """
        lang = language or "ja"
        filters_json = json.dumps(filters or {}, ensure_ascii=False)
        actual_timeout = timeout_ms or self.timeout_ms

        # Format query history for prompt
        if query_history and len(query_history) > 0:
            history_lines = [f"{i+1}. {q}" for i, q in enumerate(query_history)]
            query_history_text = "Previous queries (most recent first):\n" + "\n".join(
                history_lines
            )
        else:
            query_history_text = "No previous queries in this session."

        logger.debug(
            f"Intent extraction started: model={self.model}, timeout={actual_timeout}ms, temperature={self.temperature}"
        )
        logger.debug(
            f"Intent input: query={query!r}, language={lang}, filters={filters}, history_count={len(query_history) if query_history else 0}"
        )

        user_prompt = user_template.format(
            query=query,
            language=lang,
            query_history_text=query_history_text,
            filters_json=filters_json,
        )

        if logger.isEnabledFor(logging.DEBUG):
            from ..config import settings

            max_chars = settings.log_max_prompt_chars
            logger.debug(f"Intent system prompt: {system_prompt[:max_chars]}")
            logger.debug(f"Intent user prompt: {user_prompt[:max_chars]}")

        try:
            json_output = await self._complete(
                system=system_prompt,
                user=user_prompt,
                timeout_ms=actual_timeout,
            )
            logger.debug(f"Intent raw response: {json_output[:500]}")

            intent = IntentOutput.model_validate_json(json_output)
            logger.debug(
                f"Intent parsed successfully: normalized_query={intent.normalized_query!r}, ambiguity={intent.ambiguity}, filters={intent.filters}, followups_count={len(intent.followups)}"
            )
            return intent

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Intent extraction failed, retrying with lower temperature: {e}")
            logger.debug(
                f"Failed JSON output: {json_output if 'json_output' in locals() else 'N/A'}"
            )

            # Retry with lower temperature
            try:
                logger.debug("Retrying intent extraction with temperature=0.1")
                json_output = await self._complete(
                    system=system_prompt,
                    user=user_prompt + "\n\nREMINDER: Output ONLY valid JSON.",
                    timeout_ms=actual_timeout,
                    temperature=0.1,
                )
                logger.debug(f"Intent retry raw response: {json_output[:500]}")

                intent = IntentOutput.model_validate_json(json_output)
                logger.info(
                    f"Intent extraction retry succeeded: normalized_query={intent.normalized_query!r}"
                )
                return intent
            except Exception as retry_error:
                logger.error(f"Intent extraction retry failed: {retry_error}")
                logger.debug(
                    f"Retry failed JSON output: {json_output if 'json_output' in locals() else 'N/A'}"
                )

                # Fallback: use original query
                fallback_intent = IntentOutput(
                    normalized_query=query.strip(),
                    filters=filters,
                    followups=[],
                    ambiguity="medium",
                )
                logger.debug(f"Using fallback intent: {fallback_intent}")
                return fallback_intent

    async def compose(
        self,
        query: str,
        normalized_query: str,
        citations_data: list[dict[str, Any]],
        followups: list[str] | None = None,
        timeout_ms: int | None = None,
    ) -> ComposeOutput:
        """
        Compose brief answer from search results.
        """
        actual_timeout = timeout_ms or self.timeout_ms

        logger.debug(
            f"Compose started: model={self.model}, timeout={actual_timeout}ms, citations_count={len(citations_data)}"
        )
        logger.debug(
            f"Compose input: query={query!r}, normalized_query={normalized_query!r}, followups={followups}"
        )

        # Prepare citations text
        citations_text = self._format_citations(citations_data)
        followups_json = json.dumps(followups or [], ensure_ascii=False)

        user_prompt = COMPOSE_USER_TEMPLATE.format(
            query=query,
            normalized_query=normalized_query,
            ambiguity="medium",  # Could be passed from intent
            followups_json=followups_json,
            citations_text=citations_text,
        )

        if logger.isEnabledFor(logging.DEBUG):
            from ..config import settings

            max_chars = settings.log_max_prompt_chars
            logger.debug(f"Compose system prompt: {COMPOSE_SYSTEM_PROMPT[:max_chars]}")
            logger.debug(f"Compose user prompt: {user_prompt[:max_chars]}")
            logger.debug(f"Compose citations text (first 300 chars): {citations_text[:300]}")

        try:
            json_output = await self._complete(
                system=COMPOSE_SYSTEM_PROMPT,
                user=user_prompt,
                timeout_ms=actual_timeout,
            )
            logger.debug(f"Compose raw response: {json_output[:500]}")

            # Handle potential double-encoding or malformed JSON from LLM
            # Some models may return:
            # 1. Double-encoded: "{\\"text\\":\\"...\\"}"  (starts/ends with quotes)
            # 2. Nested object: {"text": "{\"text\":\"...\"}", "suggested_questions": [...]}
            parsed_output = json_output

            # First, try to parse to detect if text field contains JSON
            try:
                temp_obj = json.loads(json_output)
                if isinstance(temp_obj, dict) and "text" in temp_obj:
                    text_value = temp_obj["text"]
                    # Check if text field contains a JSON string
                    if isinstance(text_value, str) and (
                        text_value.startswith("{") or text_value.startswith('"')
                    ):
                        try:
                            # Try to parse the text field as JSON
                            inner_json = json.loads(text_value)
                            if isinstance(inner_json, dict) and "text" in inner_json:
                                # Text field contains a nested JSON object, extract the inner text
                                logger.warning(
                                    "Detected malformed LLM output with nested JSON in text field"
                                )
                                logger.debug(f"Malformed structure: {json_output[:200]}")
                                # Reconstruct proper JSON using inner text and outer suggested_questions
                                parsed_output = json.dumps(
                                    {
                                        "text": inner_json.get("text", ""),
                                        "suggested_questions": temp_obj.get(
                                            "suggested_questions",
                                            inner_json.get("suggested_questions", []),
                                        ),
                                    }
                                )
                                logger.debug(f"Reconstructed JSON: {parsed_output[:200]}")
                        except (json.JSONDecodeError, ValueError):
                            # text field is not valid JSON, might be double-encoded with quotes
                            pass
            except (json.JSONDecodeError, ValueError):
                # Original json_output is not valid JSON, might be double-encoded string
                if json_output.startswith('"') and json_output.endswith('"'):
                    try:
                        decoded = json.loads(json_output)
                        if isinstance(decoded, str):
                            logger.debug(
                                "Detected double-encoded JSON (quoted string), decoding..."
                            )
                            parsed_output = decoded
                    except (json.JSONDecodeError, ValueError):
                        pass

            compose = ComposeOutput.model_validate_json(parsed_output)
            logger.debug(
                f"Compose parsed successfully: text_length={len(compose.text)}, suggested_questions_count={len(compose.suggested_questions)}"
            )
            logger.debug(f"Compose answer text: {compose.text}")
            logger.debug(f"Compose suggested questions: {compose.suggested_questions}")
            return compose

        except Exception as e:
            logger.error(f"Compose failed: {e}")
            logger.debug(
                f"Failed JSON output: {json_output if 'json_output' in locals() else 'N/A'}"
            )

            # Fallback: return generic message
            fallback_compose = ComposeOutput(
                text="Results are displayed. Please review the sources for details.",
                suggested_questions=[],
            )
            logger.debug(f"Using fallback compose: {fallback_compose}")
            return fallback_compose

    def _format_citations(self, citations_data: list[dict[str, Any]]) -> str:
        """Format citations for prompt context."""
        lines = []
        for idx, cit in enumerate(citations_data[:5], start=1):  # Top 5
            title = cit.get("title", "Untitled")
            snippet = cit.get("snippet", "")[:200]  # Limit snippet length
            lines.append(f"[{idx}] {title}\n{snippet}")
        return "\n\n".join(lines) if lines else "No search results available."

    async def _complete(
        self,
        system: str,
        user: str,
        timeout_ms: int,
        temperature: float | None = None,
    ) -> str:
        """
        Call Ollama chat API and return assistant message content.
        """
        import time

        url = f"{self.base_url}/api/chat"
        actual_temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": actual_temperature,
                "top_p": self.top_p,
            },
            "stream": False,
            "keep_alive": "60m",  # Keep model loaded for 60 minutes
        }

        logger.debug(
            f"Ollama API call: url={url}, model={self.model}, temperature={actual_temperature}, top_p={self.top_p}, timeout={timeout_ms}ms"
        )
        logger.debug(
            f"Ollama payload messages: system_length={len(system)}, user_length={len(user)}"
        )

        start_time = time.time()
        try:
            response = await self.client.post(
                url,
                json=payload,
                timeout=timeout_ms / 1000.0,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.debug(
                f"Ollama response received: status={response.status_code}, elapsed={elapsed_ms}ms"
            )

            response.raise_for_status()
            data: dict[str, Any] = response.json()

            if logger.isEnabledFor(logging.DEBUG):
                from ..config import settings

                max_chars = settings.log_max_response_chars
                logger.debug(f"Ollama response data keys: {list(data.keys())}")
                logger.debug(f"Ollama response (first {max_chars} chars): {str(data)[:max_chars]}")

            message_data: dict[str, Any] = data.get("message", {})
            content: str = message_data.get("content", "")
            logger.debug(
                f"Ollama content extracted: length={len(content)}, content_preview={content[:200]}"
            )

            return content.strip()

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Ollama timeout after {elapsed_ms}ms: {e}")
            logger.debug(f"Timeout config: requested={timeout_ms}ms, elapsed={elapsed_ms}ms")
            raise TimeoutError(f"LLM timeout after {timeout_ms}ms") from e
        except httpx.HTTPStatusError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Ollama HTTP error: status={e.response.status_code}, elapsed={elapsed_ms}ms"
            )
            logger.debug(f"Ollama error response: {e.response.text[:500]}")
            raise RuntimeError(f"Ollama returned {e.response.status_code}") from e
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Ollama error after {elapsed_ms}ms: {e}")
            logger.debug(f"Ollama error details: type={type(e).__name__}, args={e.args}")
            raise

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """
        Check Ollama health status.
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=2.0)
            is_healthy = response.status_code == 200
            return (is_healthy, {"status": "ok" if is_healthy else f"HTTP {response.status_code}"})
        except Exception as e:
            return (False, {"error": str(e)})

    async def warmup(self, timeout_ms: int = 30000) -> bool:
        """
        Warm up the model by sending a dummy request.
        This loads the model into memory and keeps it warm with keep_alive.

        Args:
            timeout_ms: Timeout for warmup request (default: 30000ms = 30s)

        Returns:
            True if warmup succeeded, False otherwise
        """
        import time

        logger.info(f"Warming up Ollama model: {self.model}")
        logger.debug(f"Warmup timeout: {timeout_ms}ms")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
            ],
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            },
            "stream": False,
            "keep_alive": "60m",  # Keep model loaded for 60 minutes
        }

        start_time = time.time()
        try:
            logger.debug(f"Sending warmup request to {url}")
            response = await self.client.post(
                url,
                json=payload,
                timeout=timeout_ms / 1000.0,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.debug(f"Warmup response: status={response.status_code}, elapsed={elapsed_ms}ms")

            response.raise_for_status()
            data: dict[str, Any] = response.json()

            message_data: dict[str, Any] = data.get("message", {})
            content: str = message_data.get("content", "")

            logger.info(
                f"Warmup completed successfully: model={self.model}, "
                f"elapsed={elapsed_ms}ms, response_length={len(content)}"
            )
            logger.debug(f"Warmup response preview: {content[:100]}")

            return True

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Warmup timeout after {elapsed_ms}ms: {e}")
            return False
        except httpx.HTTPStatusError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Warmup HTTP error: status={e.response.status_code}, elapsed={elapsed_ms}ms"
            )
            logger.debug(f"Warmup error response: {e.response.text[:500]}")
            return False
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Warmup error after {elapsed_ms}ms: {e}")
            logger.debug(f"Warmup error details: type={type(e).__name__}, args={e.args}")
            return False

    async def compose_stream(
        self,
        query: str,
        normalized_query: str,
        citations_data: list[dict[str, Any]],
        followups: list[str] | None = None,
        timeout_ms: int | None = None,
    ) -> AsyncGenerator[str]:
        """
        Compose answer with streaming response.
        Yields text chunks as they are generated.
        """
        import time

        actual_timeout = timeout_ms or self.timeout_ms

        logger.debug(
            f"Compose stream started: model={self.model}, timeout={actual_timeout}ms, citations_count={len(citations_data)}"
        )
        logger.debug(
            f"Compose stream input: query={query!r}, normalized_query={normalized_query!r}"
        )

        # Prepare citations text
        citations_text = self._format_citations(citations_data)

        user_prompt = COMPOSE_USER_TEMPLATE.format(
            query=query,
            normalized_query=normalized_query,
            ambiguity="medium",
            citations_text=citations_text,
        )

        if logger.isEnabledFor(logging.DEBUG):
            from ..config import settings

            max_chars = settings.log_max_prompt_chars
            logger.debug(f"Compose stream user prompt: {user_prompt[:max_chars]}")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": COMPOSE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
            "stream": True,
            "keep_alive": "60m",  # Keep model loaded for 60 minutes
        }

        logger.debug(f"Compose stream API call: url={url}, stream=True")

        start_time = time.time()
        chunk_count = 0
        total_chars = 0

        try:
            async with self.client.stream(
                "POST",
                url,
                json=payload,
                timeout=actual_timeout / 1000.0 if actual_timeout else None,
            ) as response:
                logger.debug(f"Compose stream response started: status={response.status_code}")
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    chunk_count += 1
                                    total_chars += len(content)
                                    logger.debug(
                                        f"Compose stream chunk #{chunk_count}: length={len(content)}, total_chars={total_chars}, content={content!r}"
                                    )
                                    yield content
                            # Check if done
                            if data.get("done", False):
                                elapsed_ms = int((time.time() - start_time) * 1000)
                                logger.debug(
                                    f"Compose stream completed: chunks={chunk_count}, total_chars={total_chars}, elapsed={elapsed_ms}ms"
                                )
                                logger.debug(f"Compose stream done data: {data}")
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming line: {line[:200]}")
                            continue

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Ollama streaming timeout after {elapsed_ms}ms: {e}")
            logger.debug(
                f"Stream progress before timeout: chunks={chunk_count}, total_chars={total_chars}"
            )
            yield "[Error: Response timeout]"
        except httpx.HTTPStatusError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Ollama streaming HTTP error: status={e.response.status_code}, elapsed={elapsed_ms}ms"
            )
            try:
                # Try to read response text, but don't fail if it's a streaming response
                error_text = e.response.text[:500] if hasattr(e.response, "text") else "N/A"
                logger.debug(f"Stream error response: {error_text}")
            except Exception:
                logger.debug("Stream error response: Unable to read response body")
            yield f"[Error: HTTP {e.response.status_code}]"
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Ollama streaming error after {elapsed_ms}ms: {e}")
            logger.debug(
                f"Stream error details: type={type(e).__name__}, chunks_received={chunk_count}"
            )
            yield "[Error: Streaming failed]"

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
