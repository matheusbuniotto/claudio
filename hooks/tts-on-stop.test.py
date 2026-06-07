#!/usr/bin/env python3
"""Tests for tts-on-stop.py — clean_text logic and speak_local/speak_groq dispatch."""

import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location(
    "tts_on_stop", os.path.join(os.path.dirname(__file__), "tts-on-stop.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
clean_text = mod.clean_text
speak_local = mod.speak_local
MAX_CHARS = mod.MAX_CHARS


def test(name: str, got: str, want: str) -> bool:
    if got == want:
        print(f"  PASS  {name}")
        return True
    print(f"  FAIL  {name}")
    print(f"        got:  {repr(got)}")
    print(f"        want: {repr(want)}")
    return False


def run_clean_text_tests() -> list:
    results = []

    results.append(test(
        "strips fenced code block",
        clean_text("Here is the code:\n```python\nprint('hello')\n```\nDone."),
        "Here is the code:\n\nDone.",
    ))

    results.append(test(
        "strips inline code backticks but keeps text",
        clean_text("Run `npm install` to install."),
        "Run npm install to install.",
    ))

    results.append(test(
        "strips xml-style tags but keeps inner content",
        clean_text("I created <file>path/to/file.py</file> for you."),
        "I created path/to/file.py for you.",
    ))

    results.append(test(
        "collapses excess blank lines",
        clean_text("Line one.\n\n\n\nLine two."),
        "Line one.\n\nLine two.",
    ))

    results.append(test(
        "returns plain text unchanged",
        clean_text("The task is complete."),
        "The task is complete.",
    ))

    results.append(test(
        "returns empty string for code-only message",
        clean_text("```bash\necho hello\n```"),
        "",
    ))

    results.append(test(
        "strips multiple code blocks",
        clean_text("First:\n```js\nconsole.log(1)\n```\nSecond:\n```ts\nconst x = 2\n```\nAll done."),
        "First:\n\nSecond:\n\nAll done.",
    ))

    return results


class SpeakLocalTests(unittest.TestCase):
    @patch("subprocess.run")
    def test_calls_say_on_macos(self, mock_run):
        with patch.object(sys, "platform", "darwin"):
            speak_local("Hello world")
        mock_run.assert_called_once_with(["say", "Hello world"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_calls_espeak_on_linux(self, mock_run):
        with patch.object(sys, "platform", "linux"):
            speak_local("Hello world")
        mock_run.assert_called_once_with(["espeak", "Hello world"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_truncates_to_max_chars(self, mock_run):
        long_text = "a" * (MAX_CHARS + 100)
        with patch.object(sys, "platform", "darwin"):
            speak_local(long_text)
        called_text = mock_run.call_args[0][0][1]
        assert len(called_text) == MAX_CHARS, f"expected {MAX_CHARS}, got {len(called_text)}"
        print("  PASS  speak_local truncates to MAX_CHARS")


def run_tests() -> None:
    print("clean_text:")
    results = run_clean_text_tests()

    print("\nspeak_local:")
    suite = unittest.TestLoader().loadTestsFromTestCase(SpeakLocalTests)
    runner = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0)
    unittest_result = runner.run(suite)

    unit_passed = unittest_result.testsRun - len(unittest_result.failures) - len(unittest_result.errors)
    for failure in unittest_result.failures + unittest_result.errors:
        print(f"  FAIL  {failure[0]}")
        print(f"        {failure[1]}")
    if unit_passed == unittest_result.testsRun:
        for test_case in unittest.TestLoader().loadTestsFromTestCase(SpeakLocalTests):
            if test_case is not None:
                print(f"  PASS  {test_case._testMethodName}")

    total_passed = sum(results) + unit_passed
    total = len(results) + unittest_result.testsRun
    print(f"\n{total_passed}/{total} passed")
    if total_passed < total:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
