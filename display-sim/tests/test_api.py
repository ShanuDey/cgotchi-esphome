def valid(meta, **changes):
    return {"page": "Face", "expression": meta.expressions[0], "voice": meta.voices[0], "speaking": False,
            "accent": "#00c7ff", "secondary": "#80e6ff", "background": "#000000", "fps": 20,
            "clock_24h": False, "clock_time": "", "message_title": "Hello", "message_body": "Hi there", **changes}


def test_meta_shape(client, meta):
    body = client.get("/api/meta").json()
    assert body["expressions"] == meta.expressions
    assert body["fps"] == {"min": 5, "max": 25, "step": 5, "default": 20}
    assert body["pages"] == meta.pages == ["Face", "Clock", "Message"]
    assert set(body["themes"][0]) == {"name", "bg", "accent", "secondary"}
    assert "colors" not in body


def test_state_round_trip(client, meta):
    sent = valid(meta, expression=meta.expressions[1], fps=10)
    assert client.put("/api/state", json=sent).json() == sent
    assert client.get("/api/state").json() == sent


def test_page_settings_round_trip(client, meta):
    sent = valid(meta, page="Clock", clock_24h=True, clock_time="09:30", message_title="Note", message_body="Buy #1 milk")
    assert client.put("/api/state", json=sent).json() == sent
    assert client.get("/api/state").json() == sent


def test_unknown_page_is_422(client, meta):
    response = client.put("/api/state", json=valid(meta, page="Nope"))
    assert response.status_code == 422
    assert response.json()["detail"] == ["unknown page 'Nope'"]


def test_bad_clock_time_and_long_text_are_422(client, meta):
    two_lines = "a" + chr(10) + "b"
    response = client.put("/api/state", json=valid(meta, clock_time="25:61", message_title="x" * 17, message_body=two_lines))
    detail = response.json()["detail"]
    assert any(line.startswith("clock_time:") for line in detail)
    assert any(line.startswith("message_title:") for line in detail)
    assert any(line.startswith("message_body:") for line in detail)


def test_unknown_expression_is_422_with_text(client, meta):
    response = client.put("/api/state", json=valid(meta, expression="Nope"))
    assert response.status_code == 422
    assert response.json()["detail"] == ["unknown expression 'Nope'"]


def test_bad_hex_and_fps_are_422_with_readable_text(client, meta):
    response = client.put("/api/state", json=valid(meta, accent="red", fps=12))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert all(isinstance(line, str) for line in detail)
    assert any(line.startswith("accent:") for line in detail)
    assert "fps: fps must be 5 to 25 in steps of 5" in detail


def test_restart_is_409_when_not_managed(client):
    assert client.post("/api/restart").status_code == 409


def test_serves_the_page_and_always_revalidates_it(client):
    for path in ("/", "/app.js", "/style.css"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
