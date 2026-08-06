from demo_api.chat.config import REPO_ROOT
from demo_api.chat.priming import render_context_priming


def test_render_context_priming_surfaces_world_name_and_body() -> None:
    priming = render_context_priming(REPO_ROOT)

    assert "Crypts and Commits" in priming
    assert "Coding Assistant Continuity Framework" in priming
