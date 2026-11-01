import pytest

from simctl.face_headers import parse_enum, parse_themes


def test_load_meta_reads_the_real_headers(meta):
    assert meta.expressions and meta.voices and meta.themes
    assert "Count" not in meta.expressions


def test_parse_enum_skips_count():
    assert parse_enum("enum class Voice : uint8_t { Idle, Thinking, Count };", "Voice") == ["Idle", "Thinking"]


def test_parse_enum_missing_is_an_error():
    with pytest.raises(RuntimeError, match="Voice"):
        parse_enum("", "Voice")


def test_parse_themes_none_found_is_an_error():
    with pytest.raises(RuntimeError, match="no themes"):
        parse_themes("")


def test_parse_themes():
    (theme,) = parse_themes('{"Night", {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}}')
    assert theme.name == "Night" and theme.bg.hex == "#000000" and theme.accent.hex == "#ff0000"
    assert theme.secondary.hex == "#00ff00"
