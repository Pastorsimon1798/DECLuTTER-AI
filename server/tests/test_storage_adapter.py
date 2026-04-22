import os

import pytest

from services.storage_adapter import LocalImageStorageAdapter, create_storage_adapter_from_env


def test_storage_factory_defaults_to_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('DECLUTTER_STORAGE_BACKEND', raising=False)
    adapter = create_storage_adapter_from_env()
    assert isinstance(adapter, LocalImageStorageAdapter)


def test_storage_factory_rejects_unknown_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 'unknown')
    with pytest.raises(RuntimeError, match='Unsupported DECLUTTER_STORAGE_BACKEND'):
        create_storage_adapter_from_env()


def test_s3_backend_requires_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 's3')
    monkeypatch.delenv('DECLUTTER_S3_BUCKET', raising=False)
    with pytest.raises(RuntimeError, match='DECLUTTER_S3_BUCKET is required'):
        create_storage_adapter_from_env()
