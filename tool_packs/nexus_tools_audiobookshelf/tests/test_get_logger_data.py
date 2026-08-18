from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_logger_data as logger_data_module


def test_get_logger_data_delegates_to_logger_data_endpoint(monkeypatch):
    client = Mock()
    expected = {"logs": ["[INFO] scan complete"]}
    client.get.return_value = expected
    monkeypatch.setattr(logger_data_module, "get_client", Mock(return_value=client))

    assert logger_data_module.get_logger_data() == expected
    client.get.assert_called_once_with("logger-data")
