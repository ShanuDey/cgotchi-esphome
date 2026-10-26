from simctl.models import Settings
from simctl.settings_file import parse, render


def test_parse_is_lenient(meta):
    text = """
# a comment
expression = {expr}   # trailing comment
VOICE = {voice}
accent = #00C7FF
background = nonsense
speaking = true
this line has no equals sign
fps = 15
""".format(expr=meta.expressions[1].lower(), voice=meta.voices[1].upper())
    settings = parse(text, meta)
    assert settings.expression == meta.expressions[1]
    assert settings.voice == meta.voices[1]
    assert settings.accent == "#00c7ff"          # a leading "#" is a color, not a comment
    assert settings.background == "#000000"      # unusable: keeps its default
    assert settings.speaking is True
    assert settings.fps == 15


def test_parse_empty_gives_defaults(meta):
    settings = parse("", meta)
    assert settings.expression == meta.expressions[0]
    assert settings.accent == meta.colors[0].hex


def test_render_round_trips(meta):
    settings = Settings(expression=meta.expressions[2], voice=meta.voices[0], speaking=True, accent="#112233", fps=10)
    assert parse(render(settings), meta) == settings


def test_read_does_not_create_the_file(settings_file):
    settings_file.read()
    assert not settings_file.path.exists()


def test_ensure_then_write_replaces_atomically(settings_file, meta):
    settings_file.ensure()
    assert settings_file.path.exists()
    settings = Settings(expression=meta.expressions[1], accent="#abcdef")
    settings_file.write(settings)
    assert settings_file.read() == settings
    assert not settings_file.path.with_suffix(".tmp").exists()
