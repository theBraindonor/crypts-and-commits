import pytest
from cac.core import campaign, config, references, world
from cac.mcp import rumors as api


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Campaign")
    campaign.open_campaign(tmp_path, "c001-work")


def test_operations_and_required_body():
    with pytest.raises(TypeError):
        api.rumors_create()
    with pytest.raises(TypeError):
        api.rumors_update()
    assert api.rumors_create("[notes]", "c001")["identity"]["short"] == "c001"
    assert api.rumors_get()["body"] == "[notes]"
    assert api.rumors_list()["items"][0]["campaign"] == "c001-work"
    with pytest.raises(ValueError):
        api.rumors_create("No")
    api.rumors_update("")
    assert api.rumors_get()["body"] == ""
    assert api.rumors_delete()["campaign"] == "c001-work"
    for operation in (api.rumors_get, api.rumors_delete):
        with pytest.raises(ValueError):
            operation()


def test_budgeted_continuation_and_invalid_inputs(monkeypatch):
    text = "[tool.ruff] 🐉\r\n" * 200
    api.rumors_create(text)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 600)
    parts, cursor = [], None
    while True:
        page = api.rumors_get("c001", cursor)
        assert len(references.encoded(page)) <= 600
        parts.append(page["body"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert "".join(parts) == text
    for operation in (api.rumors_get, api.rumors_delete):
        with pytest.raises(ValueError):
            operation("../escape")
    with pytest.raises(ValueError):
        api.rumors_get(cursor="bad")
    with pytest.raises(ValueError):
        api.rumors_list("bad")
    assert api.rumors_get()["body"] == text[: len(api.rumors_get()["body"])]
