import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import main


def make_mock_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = content
    return response


# ---------------------------------------------------------------------------
# build()
# ---------------------------------------------------------------------------

class TestBuild:
    def test_returns_stripped_content(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("  some code  ")

        with patch.object(main, "client", mock_client):
            result = main.build("make a hello world script")

        assert result == "some code"

    def test_calls_correct_model(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("code")

        with patch.object(main, "client", mock_client):
            main.build("any request")

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o"

    def test_uses_correct_temperature(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("code")

        with patch.object(main, "client", mock_client):
            main.build("any request")

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["temperature"] == 0.3

    def test_sends_builder_prompt_as_system_message(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("code")

        with patch.object(main, "client", mock_client):
            main.build("any request")

        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == main.BUILDER_PROMPT

    def test_sends_user_request_as_user_message(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("code")

        with patch.object(main, "client", mock_client):
            main.build("build me a timer")

        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["content"] == "build me a timer"

    def test_api_error_propagates(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with patch.object(main, "client", mock_client):
            with pytest.raises(Exception, match="API error"):
                main.build("any request")


# ---------------------------------------------------------------------------
# main() — file saving behaviour
# ---------------------------------------------------------------------------

class TestMainFileSave:
    def test_saves_output_to_file(self, tmp_path):
        output_file = tmp_path / "output.txt"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("generated code")

        with patch.object(main, "client", mock_client):
            with patch("sys.argv", ["main.py", "build a timer", "--save", str(output_file)]):
                main.main()

        assert output_file.read_text() == "generated code"

    def test_no_save_flag_does_not_write_file(self, tmp_path, capsys):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("generated code")

        with patch.object(main, "client", mock_client):
            with patch("sys.argv", ["main.py", "build a timer"]):
                main.main()

        # Nothing written to tmp_path
        assert list(tmp_path.iterdir()) == []

    def test_output_is_printed_to_stdout(self, capsys):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_response("hello code")

        with patch.object(main, "client", mock_client):
            with patch("sys.argv", ["main.py", "build something"]):
                main.main()

        captured = capsys.readouterr()
        assert "hello code" in captured.out
