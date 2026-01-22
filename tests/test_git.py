"""Tests for git.py."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from rair.git import (
    get_commit_hash,
    get_short_hash,
    get_branch,
    get_diff,
    get_diff_hash,
    get_tracking_url,
    get_status,
    _call_git_command,
)


class TestGetCommitHash:
    def test_success(self):
        with patch("rair.git._call_git_command") as mock:
            mock.return_value = "abc123def4567890"
            result = get_commit_hash()
            assert result == "abc123def4567890"
            mock.assert_called_once_with(["rev-parse", "HEAD"], cwd=None)

    def test_error_returns_no_commit(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "git")
            result = get_commit_hash()
            assert result == "no-commit"

    def test_with_cwd(self):
        with patch("rair.git._call_git_command") as mock:
            mock.return_value = "abc123"
            result = get_commit_hash(cwd=Path("/some/path"))
            assert result == "abc123"
            mock.assert_called_once_with(["rev-parse", "HEAD"], cwd=Path("/some/path"))


class TestGetShortHash:
    def test_success(self):
        with patch("rair.git._call_git_command") as mock:
            mock.return_value = "abc1234"
            result = get_short_hash()
            assert result == "abc1234"
            mock.assert_called_once_with(["rev-parse", "--short", "HEAD"], cwd=None)

    def test_error_returns_no_commit(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "git")
            result = get_short_hash()
            assert result == "no-commit"


class TestGetBranch:
    def test_success(self):
        with patch("rair.git._call_git_command") as mock:
            mock.return_value = "main"
            result = get_branch()
            assert result == "main"
            mock.assert_called_once_with(["rev-parse", "--abbrev-ref", "HEAD"], cwd=None)

    def test_error_returns_unknown(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "git")
            result = get_branch()
            assert result == "unknown"


class TestGetDiff:
    def test_success(self):
        with patch("rair.git._call_git_command") as mock:
            mock.return_value = "diff --git a/test.py b/test.py"
            result = get_diff()
            assert result == "diff --git a/test.py b/test.py"
            mock.assert_called_once_with(["diff", "HEAD"], cwd=None)

    def test_error_returns_empty(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "git")
            result = get_diff()
            assert result == ""


class TestGetDiffHash:
    def test_empty(self):
        result = get_diff_hash("")
        assert result == ""

    def test_with_content(self):
        result = get_diff_hash("some diff content")
        assert len(result) == 20
        assert result.isalnum()


class TestGetTrackingUrl:
    def test_success(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = ["origin/main", "https://github.com/user/repo.git"]
            result = get_tracking_url()
            assert result == "https://github.com/user/repo.git"

    def test_error_returns_no_upstream(self):
        with patch("rair.git._call_git_command") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "git")
            result = get_tracking_url()
            assert result == "no-upstream"


class TestGetStatus:
    @patch("rair.git.get_tracking_url")
    @patch("rair.git.get_diff_hash")
    @patch("rair.git.get_diff")
    @patch("rair.git.get_branch")
    @patch("rair.git.get_short_hash")
    @patch("rair.git.get_commit_hash")
    def test_full_status(
        self,
        mock_hash,
        mock_short,
        mock_branch,
        mock_diff,
        mock_diff_hash,
        mock_url,
    ):
        mock_hash.return_value = "abc123def"
        mock_short.return_value = "abc123"
        mock_branch.return_value = "main"
        mock_diff.return_value = "diff content"
        mock_diff_hash.return_value = "def456"
        mock_url.return_value = "https://github.com/user/repo"

        result = get_status()

        assert result["commit_hash"] == "abc123def"
        assert result["short_hash"] == "abc123"
        assert result["branch"] == "main"
        assert result["diff"] == "diff content"
        assert result["diff_hash"] == "def456"
        assert result["tracking_url"] == "https://github.com/user/repo"

    @patch("rair.git.get_tracking_url")
    @patch("rair.git.get_diff_hash")
    @patch("rair.git.get_diff")
    @patch("rair.git.get_branch")
    @patch("rair.git.get_short_hash")
    @patch("rair.git.get_commit_hash")
    def test_full_status_with_cwd(
        self,
        mock_hash,
        mock_short,
        mock_branch,
        mock_diff,
        mock_diff_hash,
        mock_url,
    ):
        mock_hash.return_value = "abc123def"
        mock_short.return_value = "abc123"
        mock_branch.return_value = "main"
        mock_diff.return_value = "diff content"
        mock_diff_hash.return_value = "def456"
        mock_url.return_value = "https://github.com/user/repo"

        result = get_status(cwd=Path("/some/path"))

        assert result["commit_hash"] == "abc123def"
        mock_hash.assert_called_once_with(Path("/some/path"))