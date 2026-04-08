from nexus.benchmark_media_household import DEFAULT_SHOWS, build_steps


def test_build_steps_contains_expected_targets() -> None:
    steps = build_steps()
    names = [step.name for step in steps]

    for show in DEFAULT_SHOWS:
        assert f"tautulli:{show}" in names
    assert 'n8n:aCc9YEwBJ59sXPqE' in names
    assert 'n8n:lFLvRtjncYmDpNQu' in names
    assert 'sonarr:The Boys' in names
