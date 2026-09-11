from translator import history


def test_append_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "h.json")
    history.append_entry("en", "es", "hello", "hola")
    entries = history.load_recent(limit=5)
    assert len(entries) == 1
    assert entries[0]["source_text"] == "hello"
    assert entries[0]["translated_text"] == "hola"


def test_load_recent_respects_cap_and_order(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "h.json")
    for i in range(25):
        history.append_entry("en", "es", f"text{i}", f"texto{i}")
    recent = history.load_recent(limit=3)
    assert len(recent) == 3
    assert recent[0]["source_text"] == "text24"
    assert len(history._load_all()) == history.MAX_ENTRIES
