def valid(meta, **changes):
    return {"expression": meta.expressions[0], "voice": meta.voices[0], "speaking": False,
            "accent": "#00c7ff", "background": "#000000", "fps": 20, **changes}


def test_meta_shape(client, meta):
    body = client.get("/api/meta").json()
    assert body["expressions"] == meta.expressions
    assert body["fps"] == {"min": 5, "max": 25, "step": 5, "default": 20}
    assert set(body["themes"][0]) == {"name", "bg", "accent"}
    assert len(body["colors"][0]["rgb"]) == 3


def test_state_round_trip(client, meta):
    sent = valid(meta, expression=meta.expressions[1], fps=10)
    assert client.put("/api/state", json=sent).json() == sent
    assert client.get("/api/state").json() == sent


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


def test_serves_the_page(client):
    assert client.get("/").status_code == 200
