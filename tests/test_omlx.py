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

    def test_load_config_invalid_json(self):
        """load_config returns empty dict when file contains invalid JSON.

        NOTE: Noticed the original tests didn't cover corrupted config files.
        This is a realistic edge case (e.g. interrupted write), so adding it.
        """
        with open(self.config_path, "w") as fh:
            fh.write("{not valid json")
        with patch("omlx.CONFIG_PATH", self.config_path):
            cfg = omlx.load_config()
        self.assertEqual(cfg, {})


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
