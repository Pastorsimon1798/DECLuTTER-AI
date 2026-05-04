"""Tests for the provider-agnostic analysis adapter factory."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.services.analysis_adapter import (
    AnalysisResult,
    AnthropicAnalysisAdapter,
    FallbackAnalysisAdapter,
    LMStudioNativeAnalysisAdapter,
    MockStructuredAnalysisAdapter,
    OllamaAnalysisAdapter,
    OpenAICompatibleAnalysisAdapter,
    create_analysis_adapter_from_env,
)
from app.schemas.analysis import DetectedItem


class TestCreateAnalysisAdapterFromEnv:
    def test_defaults_to_mock_when_no_env_set(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, MockStructuredAnalysisAdapter)

    def test_mock_provider_explicit(self) -> None:
        with patch.dict(os.environ, {"DECLUTTER_ANALYSIS_PROVIDER": "mock"}, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, MockStructuredAnalysisAdapter)

    def test_openai_compatible_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4o-mini",
            "OPENAI_API_KEY": "sk-test",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert adapter.base_url == "https://api.openai.com/v1"
        assert adapter.model == "gpt-4o-mini"
        assert adapter.api_key == "sk-test"

    def test_groq_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "groq",
            "DECLUTTER_INFERENCE_BASE_URL": "https://api.groq.com/openai/v1",
            "DECLUTTER_INFERENCE_MODEL": "llama-3.2-90b-vision-preview",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert adapter.base_url == "https://api.groq.com/openai/v1"
        assert adapter.model == "llama-3.2-90b-vision-preview"

    def test_lmstudio_provider_sets_default_url(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "lmstudio",
            "DECLUTTER_INFERENCE_MODEL": "my-local-model",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, LMStudioNativeAnalysisAdapter)
        # Native adapter strips the /v1 suffix
        assert adapter.base_url == "http://127.0.0.1:1234"
        assert adapter.model == "my-local-model"

    def test_anthropic_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "ANTHROPIC_MODEL": "claude-3-5-sonnet",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, AnthropicAnalysisAdapter)
        assert adapter.base_url == "https://api.anthropic.com"
        assert adapter.model == "claude-3-5-sonnet"
        assert adapter.api_key == "sk-ant-test"

    def test_claude_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "claude",
            "DECLUTTER_INFERENCE_BASE_URL": "https://custom.anthropic.com",
            "DECLUTTER_INFERENCE_MODEL": "claude-3-opus",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, AnthropicAnalysisAdapter)
        assert adapter.base_url == "https://custom.anthropic.com"

    def test_ollama_native_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "ollama-native",
            "OLLAMA_MODEL": "llava",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OllamaAnalysisAdapter)
        assert adapter.base_url == "http://127.0.0.1:11434"
        assert adapter.model == "llava"

    def test_ollama_direct_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "ollama_direct",
            "DECLUTTER_INFERENCE_BASE_URL": "http://ollama.local:11434",
            "DECLUTTER_INFERENCE_MODEL": "llava-phi3",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OllamaAnalysisAdapter)
        assert adapter.base_url == "http://ollama.local:11434"

    def test_unrecognized_provider_with_config_falls_back_to_openai_compatible(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "custom-provider",
            "DECLUTTER_INFERENCE_BASE_URL": "https://custom.ai/v1",
            "DECLUTTER_INFERENCE_MODEL": "custom-model",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert adapter.base_url == "https://custom.ai/v1"
        assert adapter.model == "custom-model"

    def test_unrecognized_provider_without_config_falls_back_to_mock(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "unknown",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, MockStructuredAnalysisAdapter)

    def test_legacy_declutter_model_provider_env_var(self) -> None:
        env = {
            "DECLUTTER_MODEL_PROVIDER": "openai",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4o",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)

    def test_analysis_provider_takes_precedence_over_model_provider(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "anthropic",
            "DECLUTTER_MODEL_PROVIDER": "openai",
            "ANTHROPIC_MODEL": "claude-3-haiku",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, AnthropicAnalysisAdapter)
        assert adapter.model == "claude-3-haiku"

    def test_openai_compatible_respects_timeout_and_max_tokens(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4o-mini",
            "DECLUTTER_INFERENCE_TIMEOUT_SECONDS": "30",
            "DECLUTTER_INFERENCE_MAX_TOKENS": "512",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert adapter.timeout_seconds == 30.0
        assert adapter.max_tokens == 512

    def test_fallback_wraps_primary_when_allow_local_set(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "DECLUTTER_INFERENCE_BASE_URL": "https://api.openai.com/v1",
            "DECLUTTER_INFERENCE_MODEL": "gpt-4o-mini",
            "DECLUTTER_INFERENCE_API_KEY": "sk-test",
            "DECLUTTER_INFERENCE_ALLOW_LOCAL": "1",
            "DECLUTTER_INFERENCE_FALLBACK_URL": "http://host.docker.internal:8085/v1",
            "DECLUTTER_INFERENCE_FALLBACK_MODEL": "Qwen3.5-0.8B-Q4_K_M",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, FallbackAnalysisAdapter)
        assert isinstance(adapter._primary, OpenAICompatibleAnalysisAdapter)
        assert isinstance(adapter._fallback, OpenAICompatibleAnalysisAdapter)
        assert adapter._fallback.base_url == "http://host.docker.internal:8085/v1"
        assert adapter._fallback.model == "Qwen3.5-0.8B-Q4_K_M"

    def test_no_fallback_without_allow_local(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "DECLUTTER_INFERENCE_BASE_URL": "https://api.openai.com/v1",
            "DECLUTTER_INFERENCE_MODEL": "gpt-4o-mini",
            "DECLUTTER_INFERENCE_FALLBACK_URL": "http://host.docker.internal:8085/v1",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert not isinstance(adapter, FallbackAnalysisAdapter)

    def test_no_fallback_without_fallback_url(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "DECLUTTER_INFERENCE_BASE_URL": "https://api.openai.com/v1",
            "DECLUTTER_INFERENCE_MODEL": "gpt-4o-mini",
            "DECLUTTER_INFERENCE_ALLOW_LOCAL": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, OpenAICompatibleAnalysisAdapter)
        assert not isinstance(adapter, FallbackAnalysisAdapter)

    def test_fallback_model_defaults_to_primary_model(self) -> None:
        env = {
            "DECLUTTER_ANALYSIS_PROVIDER": "openai",
            "DECLUTTER_INFERENCE_BASE_URL": "https://api.openai.com/v1",
            "DECLUTTER_INFERENCE_MODEL": "gpt-4o-mini",
            "DECLUTTER_INFERENCE_ALLOW_LOCAL": "1",
            "DECLUTTER_INFERENCE_FALLBACK_URL": "http://localhost:8085/v1",
        }
        with patch.dict(os.environ, env, clear=True):
            adapter = create_analysis_adapter_from_env()
        assert isinstance(adapter, FallbackAnalysisAdapter)
        assert adapter._fallback.model == "gpt-4o-mini"


class TestFallbackAnalysisAdapter:
    """Tests for the FallbackAnalysisAdapter failover logic."""

    @staticmethod
    def _make_result(label: str) -> AnalysisResult:
        return AnalysisResult(
            items=[DetectedItem(label=label, confidence=0.9, estimated_value_usd=5.0)],
            engine="test",
            structured_output_version="test-v1",
            total_estimated_value_usd=5.0,
        )

    def test_primary_succeeds_no_fallback(self) -> None:
        result = self._make_result("primary-item")
        primary = MockStructuredAnalysisAdapter()
        fallback = MockStructuredAnalysisAdapter()
        adapter = FallbackAnalysisAdapter(
            primary=primary,
            fallback=fallback,
            primary_name="cloud",
            fallback_name="local",
        )
        # MockStructuredAnalysisAdapter always succeeds, so patch primary.run
        with patch.object(primary, "run", return_value=result):
            output = adapter.run("test-key")
        assert output.items[0].label == "primary-item"

    def test_fallback_on_primary_failure(self) -> None:
        result = self._make_result("fallback-item")
        primary = MockStructuredAnalysisAdapter()
        fallback = MockStructuredAnalysisAdapter()
        adapter = FallbackAnalysisAdapter(
            primary=primary,
            fallback=fallback,
            primary_name="cloud",
            fallback_name="local",
        )
        with patch.object(primary, "run", side_effect=RuntimeError("cloud down")):
            with patch.object(fallback, "run", return_value=result):
                output = adapter.run("test-key")
        assert output.items[0].label == "fallback-item"

    def test_raises_if_both_fail(self) -> None:
        primary = MockStructuredAnalysisAdapter()
        fallback = MockStructuredAnalysisAdapter()
        adapter = FallbackAnalysisAdapter(
            primary=primary,
            fallback=fallback,
            primary_name="cloud",
            fallback_name="local",
        )
        with patch.object(primary, "run", side_effect=RuntimeError("cloud down")):
            with patch.object(fallback, "run", side_effect=RuntimeError("local down")):
                with pytest.raises(RuntimeError, match="local down"):
                    adapter.run("test-key")
