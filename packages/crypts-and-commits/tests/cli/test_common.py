import io
import sys

import pytest
from cac.cli.common import configure_output_encoding


def test_configure_output_encoding_switches_cp1252_stream_to_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    # A default CliRunner/StringIO capture buffer is UTF-8 and would pass even
    # with the bug present, so reproduce the real failure mode: a stream whose
    # encoding is cp1252 (the Windows legacy code page) cannot encode U+2192.
    assert "→".encode("cp1252", errors="ignore") == b""  # sanity: unencodable in cp1252

    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))
    monkeypatch.setattr(sys, "stderr", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))

    configure_output_encoding()

    assert sys.stdout.encoding.lower() == "utf-8"
    assert sys.stderr.encoding.lower() == "utf-8"

    # The arrow that crashed `cac ... get` on Windows now round-trips.
    sys.stdout.write("→")
    sys.stdout.flush()
    assert "→".encode() in raw.getvalue()


def test_configure_output_encoding_ignores_streams_without_reconfigure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Streams that are not TextIOWrapper (e.g. test-capture buffers) have no
    # reconfigure(); the helper must skip them, not raise.
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    configure_output_encoding()  # must not raise
