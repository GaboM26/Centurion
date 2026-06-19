"""Tests for the Centurion entry point."""

import builtins
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main as centurion_main


def test_main_defaults_to_menu_in_tty(monkeypatch, capsys) -> None:
    centurion_main.get_settings.cache_clear()
    monkeypatch.setattr(centurion_main.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": "6")

    exit_code = centurion_main.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Centurion menu" in captured.out
    assert "Exiting Centurion." in captured.out


def test_main_defaults_to_configuration_summary_without_tty(monkeypatch, capsys) -> None:
    centurion_main.get_settings.cache_clear()
    monkeypatch.setattr(centurion_main.sys.stdin, "isatty", lambda: False)

    exit_code = centurion_main.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Centurion configuration" in captured.out
    assert "Centurion menu" not in captured.out


def test_main_preview_result_runs_without_menu(capsys) -> None:
    exit_code = centurion_main.main(["preview-result"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Sample OrderResult" in captured.out
    assert "Centurion menu" not in captured.out


def test_main_runs_interactive_menu_when_flag_is_passed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(centurion_main.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": "6")

    exit_code = centurion_main.main(["--menu"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Centurion menu" in captured.out
    assert "Exiting Centurion." in captured.out


def test_main_runs_interactive_menu_when_enabled_in_settings(monkeypatch, capsys) -> None:
    monkeypatch.setenv("CENTURION_ENABLE_TEST_MENU", "true")
    centurion_main.get_settings.cache_clear()
    monkeypatch.setattr(centurion_main.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": "6")

    exit_code = centurion_main.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Centurion menu" in captured.out


def test_main_skips_menu_when_disabled_in_settings(monkeypatch, capsys) -> None:
    monkeypatch.setenv("CENTURION_ENABLE_TEST_MENU", "false")
    centurion_main.get_settings.cache_clear()
    monkeypatch.setattr(centurion_main.sys.stdin, "isatty", lambda: True)

    exit_code = centurion_main.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Centurion configuration" in captured.out
    assert "Centurion menu" not in captured.out
