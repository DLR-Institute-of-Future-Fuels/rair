"""Tests for script_type.py."""

import tempfile
from pathlib import Path

from rair.script_type import (
    detect_script_type,
    get_command_args
)


class TestDetectScriptType:
    def test_python_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello')")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_bash_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("echo 'hello'")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "bash"
        finally:
            script_path.unlink()

    def test_exe_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".exe") as f:
            f.write("executable content")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_bat_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bat") as f:
            f.write("@echo off")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_cmd_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cmd") as f:
            f.write("@echo off")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_python_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/usr/bin/env python\nprint('hello')")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_python3_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/usr/bin/python3\nprint('hello')")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_bash_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/bin/bash\necho 'hello'")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "bash"
        finally:
            script_path.unlink()

    def test_shebang_extension_takes_precedence(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("#!/bin/bash\necho 'hello'")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_no_extension_no_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("some random content")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_unrecognized_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".unknown") as f:
            f.write("content")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()


class TestGetCommandArgs:
    def test_python_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello')")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "python")
            assert result == ["python", str(script_path)]
        finally:
            script_path.unlink()

    def test_bash_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("echo 'hello'")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "bash")
            assert result == ["bash", str(script_path)]
        finally:
            script_path.unlink()

    def test_other_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("executable content")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "other")
            assert result == [str(script_path)]
        finally:
            script_path.unlink()
