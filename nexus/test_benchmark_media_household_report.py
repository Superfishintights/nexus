from nexus.benchmark_media_household_report import render_media_household_markdown


def test_render_media_household_markdown_includes_core_sections() -> None:
    markdown = render_media_household_markdown(
        {
            'generatedAt': '2026-01-01T00:00:00Z',
            'serial': {'wallMs': 1000},
            'parallel': {
                'wallMs': 400,
                'steps': [
                    {'name': 'tautulli:How I Met Your Mother', 'category': 'tautulli', 'result': {'user': 'u', 'show': 'How I Met Your Mother', 'days': 2, 'entries': 4, 'avgHoursPerDay': 1.5, 'avgEpisodesPerDay': 2.0}},
                    {'name': 'sonarr:The Boys', 'category': 'sonarr', 'result': {'isAdded': False, 'matches': []}},
                    {'name': 'n8n:a', 'category': 'n8n', 'result': {'name': 'wf', 'active': True, 'triggerCount': 1, 'latestSuccessfulExecution': {'status': 'success', 'id': '1'}, 'executionMode': 'latest_success_summary'}},
                ],
            },
        },
        {
            'serialMeanMs': 1100,
            'serialMedianMs': 1000,
            'parallelMeanMs': 500,
            'parallelMedianMs': 450,
            'runs': [{'run': 1, 'serialWallMs': 1000, 'parallelWallMs': 450}],
        },
    )

    assert 'Media household benchmark report' in markdown
    assert 'Parallel speedup' in markdown
    assert 'How I Met Your Mother' in markdown
    assert 'The Boys' in markdown
    assert 'Repeatability' in markdown
