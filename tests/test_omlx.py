"""Tests for omlx.py — model alias manager."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import omlx


class TestConfig(unittest.TestCase):
    """Tests for load_config and save_config."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.tmp.close()
        self.config_path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_load_config_missing_file(self):
        """load_config returns empty dict when file does not exist."""
        os.unlink(self.config_path)
        with patch("omlx.CONFIG_PATH", self.config_path):
            cfg = omlx.load_config()
        self.assertEqual(cfg, {})

    def test_load_config_empty_file(self):
        """load_config returns empty dict for an empty file."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            cfg = omlx.load_config()
        self.assertEqual(cfg, {})

    def test_save_and_load_roundtrip(self):
        """save_config persists data that load_config can read back."""
        data = {"aliases": {"gpt4": "openai/gpt-4"}}
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.save_config(data)
            cfg = omlx.load_config()
        self.assertEqual(cfg, data)

    def test_save_config_creates_valid_json(self):
        """save_config writes valid JSON to disk."""
        data = {"aliases": {"llama": "meta/llama-3"}}
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.save_config(data)
        with open(self.config_path) as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk, data)


class TestCmdAdd(unittest.TestCase):
    """Tests for cmd_add."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.tmp.close()
        self.config_path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_add_new_alias(self):
        """cmd_add stores a new alias."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.cmd_add("gpt4", "openai/gpt-4")
            cfg = omlx.load_config()
        self.assertEqual(cfg.get("aliases", {}).get("gpt4"), "openai/gpt-4")

    def test_add_overwrites_existing_alias(self):
        """cmd_add updates the model when alias already exists."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.cmd_add("gpt4", "openai/gpt-4")
            omlx.cmd_add("gpt4", "openai/gpt-4-turbo")
            cfg = omlx.load_config()
        self.assertEqual(cfg["aliases"]["gpt4"], "openai/gpt-4-turbo")


class TestCmdRemove(unittest.TestCase):
    """Tests for cmd_remove."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.tmp.close()
        self.config_path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_remove_existing_alias(self):
        """cmd_remove deletes an alias that exists."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.cmd_add("llama", "meta/llama-3")
            omlx.cmd_remove("llama")
            cfg = omlx.load_config()
        self.assertNotIn("llama", cfg.get("aliases", {}))

    def test_remove_nonexistent_alias_no_error(self):
        """cmd_remove does not raise when alias is absent."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            try:
                omlx.cmd_remove("nonexistent")
            except Exception as exc:  # pragma: no cover
                self.fail(f"cmd_remove raised unexpectedly: {exc}")


class TestCmdList(unittest.TestCase):
    """Tests for cmd_list."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.tmp.close()
        self.config_path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_list_shows_aliases(self, capsys=None):
        """cmd_list prints registered aliases without raising."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.cmd_add("gpt4", "openai/gpt-4")
            omlx.cmd_add("llama", "meta/llama-3")
            # Should not raise
            omlx.cmd_list()

    def test_list_empty_config(self):
        """cmd_list handles an empty config gracefully."""
        with patch("omlx.CONFIG_PATH", self.config_path):
            omlx.cmd_list()  # should not raise


if __name__ == "__main__":
    unittest.main()
