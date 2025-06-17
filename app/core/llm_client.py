import json
import logging
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import litellm
    from litellm import acompletion

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class LLMClient:
    """
    Unified LLM client using LiteLLM for multiple model providers
    """

    def __init__(self):
        self.is_available = LITELLM_AVAILABLE

        if not LITELLM_AVAILABLE:
            logger.warning(
                "LiteLLM is not installed. Install with: pip install litellm"
            )
            return

        # Configure LiteLLM settings
        self._configure_litellm()

        # Set default models
        self.default_model = getattr(settings, "DEFAULT_LLM_MODEL", "gpt-4o-mini")
        self.embedding_model = getattr(
            settings, "DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small"
        )

        logger.info(f"LLM Client initialized with default model: {self.default_model}")

    def _configure_litellm(self):
        """Configure LiteLLM with API keys and settings"""
        try:
            # Set API keys
            if hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY:
                litellm.openai_key = settings.OPENAI_API_KEY

            if hasattr(settings, "ANTHROPIC_API_KEY") and settings.ANTHROPIC_API_KEY:
                litellm.anthropic_key = settings.ANTHROPIC_API_KEY

            if hasattr(settings, "GOOGLE_API_KEY") and settings.GOOGLE_API_KEY:
                litellm.google_key = settings.GOOGLE_API_KEY

            if hasattr(settings, "COHERE_API_KEY") and settings.COHERE_API_KEY:
                litellm.cohere_key = settings.COHERE_API_KEY

            # Configure Azure if available
            if hasattr(settings, "AZURE_API_KEY") and settings.AZURE_API_KEY:
                litellm.azure_key = settings.AZURE_API_KEY
                if hasattr(settings, "AZURE_API_BASE"):
                    litellm.azure_api_base = settings.AZURE_API_BASE
                if hasattr(settings, "AZURE_API_VERSION"):
                    litellm.azure_api_version = settings.AZURE_API_VERSION

            # Set global settings
            litellm.set_verbose = getattr(settings, "LITELLM_VERBOSE", False)
            litellm.drop_params = True  # Drop unsupported parameters automatically

        except Exception as e:
            logger.error(f"Error configuring LiteLLM: {e}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Create a chat completion using LiteLLM

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format specification
            stream: Whether to stream the response
            **kwargs: Additional model-specific parameters

        Returns:
            Chat completion response or async generator for streaming
        """
        if not self.is_available:
            raise RuntimeError("LiteLLM is not available. Please install it first.")

        model = model or self.default_model

        try:
            # Prepare parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs,
            }

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            if response_format is not None:
                params["response_format"] = response_format

            logger.debug(f"Making chat completion request with model: {model}")

            # Make the request
            if stream:
                return await self._stream_completion(params)
            else:
                response = await acompletion(**params)
                logger.debug(f"Chat completion successful with model: {model}")
                return response

        except Exception as e:
            logger.error(f"Error in chat completion with model {model}: {e}")
            raise

    async def _stream_completion(
        self, params: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming completion"""
        try:
            response = await acompletion(**params)
            async for chunk in response:
                yield chunk
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def extract_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extract JSON response from LLM with automatic parsing

        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Parsed JSON response
        """
        try:
            response = await self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs,
            )

            content = response.choices[0].message.content

            # Try to parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                # Try to extract JSON from the content
                return self._extract_json_from_text(content)

        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            raise

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that might contain additional content"""
        import re

        # Try to find JSON blocks
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # If no valid JSON found, return error structure
        return {
            "error": "Could not extract valid JSON from response",
            "raw_content": text,
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embedding(
        self, text: Union[str, List[str]], model: Optional[str] = None, **kwargs
    ) -> List[float]:
        """
        Generate embeddings for text using LiteLLM

        Args:
            text: Text or list of texts to embed
            model: Embedding model to use
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        if not self.is_available:
            raise RuntimeError("LiteLLM is not available. Please install it first.")

        model = model or self.embedding_model

        try:
            from litellm import aembedding

            # Ensure text is a list
            if isinstance(text, str):
                text = [text]

            response = await aembedding(model=model, input=text, **kwargs)

            # Extract embeddings
            embeddings = response.data[0]["embedding"]

            logger.debug(f"Generated {len(embeddings)} embeddings using model: {model}")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings with model {model}: {e}")
            raise

    async def classify_text(
        self,
        text: str,
        categories: List[str],
        model: Optional[str] = None,
        include_confidence: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Classify text into predefined categories

        Args:
            text: Text to classify
            categories: List of possible categories
            model: Model to use for classification
            include_confidence: Whether to include confidence scores
            **kwargs: Additional parameters

        Returns:
            Classification result with category and optional confidence
        """
        system_prompt = f"""
        You are a text classification system. Classify the given text into one of these categories:
        {', '.join(categories)}
        
        Respond with a JSON object containing:
        - "category": the most appropriate category
        - "confidence": confidence score between 0.0 and 1.0 (if requested)
        - "reasoning": brief explanation of the classification
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this text: {text}"},
        ]

        result = await self.extract_json(messages=messages, model=model, **kwargs)

        # Validate category
        predicted_category = result.get("category", "")
        if predicted_category not in categories:
            logger.warning(f"Model predicted invalid category: {predicted_category}")
            result["category"] = categories[0]  # Default to first category
            result["confidence"] = 0.1  # Low confidence for invalid prediction

        return result

    def get_available_models(self) -> List[str]:
        """
        Get list of available models based on configured API keys
        """
        models = []

        # OpenAI models
        if hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY:
            models.extend(
                [
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "text-embedding-3-large",
                    "text-embedding-3-small",
                ]
            )

        # Anthropic models
        if hasattr(settings, "ANTHROPIC_API_KEY") and settings.ANTHROPIC_API_KEY:
            models.extend(
                [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                ]
            )

        # Google models
        if hasattr(settings, "GOOGLE_API_KEY") and settings.GOOGLE_API_KEY:
            models.extend(
                [
                    "gemini-1.5-pro",
                    "gemini-1.5-flash",
                    "gemini-pro",
                    "text-embedding-004",
                ]
            )

        # Add other providers as needed

        return models

    async def test_connection(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Test connection to LLM service

        Args:
            model: Model to test (defaults to default model)

        Returns:
            Test result with status and details
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "LiteLLM is not available",
                "available": False,
            }

        model = model or self.default_model

        try:
            messages = [
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'Connection successful.'",
                }
            ]

            response = await self.chat_completion(
                messages=messages, model=model, max_tokens=50
            )

            content = response.choices[0].message.content

            return {
                "status": "success",
                "message": f"Successfully connected to {model}",
                "response": content,
                "available": True,
                "model": model,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to {model}: {str(e)}",
                "available": False,
                "model": model,
            }


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get the global LLM client instance (singleton pattern)

    Returns:
        LLMClient instance
    """
    global _llm_client

    if _llm_client is None:
        _llm_client = LLMClient()

    return _llm_client
