from simctl.models import Settings
from simctl.settings_file import parse, render


def test_parse_is_lenient(meta):
    text = """
# a comment
expression = {expr}   # trailing comment
VOICE = {voice}
accent = #00C7FF
secondary = #112233 # a comment
background = nonsense
page = clock
clock_24h = on
clock_time = 07:05
message_title = Buy #1 # not a comment
message_body = {long}
speaking = true
this line has no equals sign
fps = 15
""".format(expr=meta.expressions[1].lower(), voice=meta.voices[1].upper(), long="x" * 200)
    settings = parse(text, meta)
    assert settings.expression == meta.expressions[1]
    assert settings.voice == meta.voices[1]
    assert settings.accent == "#00c7ff"          # a leading "#" is a color, not a comment
    assert settings.background == "#000000"      # unusable: keeps its default
    assert settings.speaking is True
    assert settings.fps == 15
    assert settings.secondary == "#112233"
    assert settings.page == "Clock"
    assert settings.clock_24h is True and settings.clock_time == "07:05"
    assert settings.message_title == "Buy #1 # not a comment"[:16]   # text is literal, cut to the device's limit
    assert settings.message_body == "x" * 120


def test_parse_ignores_an_out_of_range_or_off_step_fps(meta):
    assert parse("fps = 99", meta).fps == 20
    assert parse("fps = 12", meta).fps == 20
    assert parse("fps = 10", meta).fps == 10


def test_parse_ignores_a_bad_clock_time(meta):
    assert parse("clock_time = 99:99", meta).clock_time == ""


def test_parse_empty_gives_defaults(meta):
    settings = parse("", meta)
    assert settings.expression == meta.expressions[0]
    assert settings.accent == meta.themes[0].accent.hex


def test_render_round_trips(meta):
    settings = Settings(page="Message", expression=meta.expressions[2], voice=meta.voices[0], speaking=True, accent="#112233",
                        secondary="#445566", fps=10, clock_24h=True, clock_time="23:59", message_title="Hi", message_body="a b")
    assert parse(render(settings), meta) == settings


def test_read_does_not_create_the_file(settings_file):
    settings_file.read()
    assert not settings_file.path.exists()


def test_ensure_then_write_replaces_atomically(settings_file, meta):
    settings_file.ensure()
    assert settings_file.path.exists()
    settings = Settings(expression=meta.expressions[1], accent="#abcdef", secondary="#fedcba")
    settings_file.write(settings)
    assert settings_file.read() == settings
    assert not settings_file.path.with_suffix(".tmp").exists()
