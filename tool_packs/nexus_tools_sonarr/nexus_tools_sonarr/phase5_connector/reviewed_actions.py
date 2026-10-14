"""Human-reviewed Sonarr action metadata inputs.

These names are compatibility identities, not classification signals.  The
manifest builder requires every exported tool to appear in exactly one
reviewed category and writes explicit metadata onto every immutable entry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionReview:
    action_class: str
    impact: str


# The read-only surface was reviewed endpoint-by-endpoint.  It is intentionally
# explicit so a future POST called ``get_*`` cannot gain observe authority.
OBSERVE_TOOLS = frozenset(
    {
        "sonarr.get_autotagging", "sonarr.get_autotagging_by_id", "sonarr.get_autotagging_schema",
        "sonarr.get_blocklist", "sonarr.get_calendar", "sonarr.get_calendar_by_id",
        "sonarr.get_command", "sonarr.get_command_by_id", "sonarr.get_config_downloadclient",
        "sonarr.get_config_downloadclient_by_id", "sonarr.get_config_host",
        "sonarr.get_config_host_by_id", "sonarr.get_config_importlist",
        "sonarr.get_config_importlist_by_id", "sonarr.get_config_indexer",
        "sonarr.get_config_indexer_by_id", "sonarr.get_config_mediamanagement",
        "sonarr.get_config_mediamanagement_by_id", "sonarr.get_config_naming",
        "sonarr.get_config_naming_by_id", "sonarr.get_config_naming_examples",
        "sonarr.get_config_ui", "sonarr.get_config_ui_by_id", "sonarr.get_customfilter",
        "sonarr.get_customfilter_by_id", "sonarr.get_customformat", "sonarr.get_customformat_by_id",
        "sonarr.get_customformat_schema", "sonarr.get_delayprofile", "sonarr.get_delayprofile_by_id",
        "sonarr.get_diskspace", "sonarr.get_downloadclient", "sonarr.get_downloadclient_by_id",
        "sonarr.get_downloadclient_schema", "sonarr.get_episode", "sonarr.get_episode_by_id",
        "sonarr.get_episodefile", "sonarr.get_episodefile_by_id", "sonarr.get_filesystem",
        "sonarr.get_filesystem_mediafiles", "sonarr.get_filesystem_type", "sonarr.get_health",
        "sonarr.get_history", "sonarr.get_history_series", "sonarr.get_history_since",
        "sonarr.get_importlist", "sonarr.get_importlist_by_id", "sonarr.get_importlist_schema",
        "sonarr.get_importlistexclusion_by_id", "sonarr.get_importlistexclusion_paged",
        "sonarr.get_indexer", "sonarr.get_indexer_by_id", "sonarr.get_indexer_schema",
        "sonarr.get_indexerflag", "sonarr.get_language", "sonarr.get_language_by_id",
        "sonarr.get_languageprofile_by_id", "sonarr.get_localization",
        "sonarr.get_localization_by_id", "sonarr.get_localization_language", "sonarr.get_log",
        "sonarr.get_log_file", "sonarr.get_log_file_by_filename", "sonarr.get_log_file_update",
        "sonarr.get_log_file_update_by_filename", "sonarr.get_manualimport",
        "sonarr.get_mediacover_by_series_id_by_filename", "sonarr.get_metadata",
        "sonarr.get_metadata_by_id", "sonarr.get_metadata_schema", "sonarr.get_notification",
        "sonarr.get_notification_by_id", "sonarr.get_notification_schema", "sonarr.get_parse",
        "sonarr.get_ping", "sonarr.get_qualitydefinition", "sonarr.get_qualitydefinition_by_id",
        "sonarr.get_qualitydefinition_limits", "sonarr.get_qualityprofile",
        "sonarr.get_qualityprofile_by_id", "sonarr.get_qualityprofile_schema", "sonarr.get_queue",
        "sonarr.get_queue_details", "sonarr.get_queue_status", "sonarr.get_release",
        "sonarr.get_releaseprofile", "sonarr.get_releaseprofile_by_id",
        "sonarr.get_remotepathmapping", "sonarr.get_remotepathmapping_by_id", "sonarr.get_rename",
        "sonarr.get_rootfolder", "sonarr.get_rootfolder_by_id", "sonarr.get_series",
        "sonarr.get_series_by_id", "sonarr.get_series_by_id_folder", "sonarr.get_series_lookup",
        "sonarr.get_system_backup", "sonarr.get_system_routes", "sonarr.get_system_routes_duplicate",
        "sonarr.get_system_status", "sonarr.get_system_task", "sonarr.get_system_task_by_id",
        "sonarr.get_tag", "sonarr.get_tag_by_id", "sonarr.get_tag_detail",
        "sonarr.get_tag_detail_by_id", "sonarr.get_update", "sonarr.get_wanted_cutoff",
        "sonarr.get_wanted_cutoff_by_id", "sonarr.get_wanted_missing",
        "sonarr.get_wanted_missing_by_id", "sonarr.head_ping", "sonarr.list_season_releases",
    }
)

# Operations that can trigger downstream work or service-side processing.
EXTERNAL_EFFECT_TOOLS = frozenset(
    {
        "sonarr.create_command", "sonarr.create_history_failed_by_id", "sonarr.create_manualimport",
        "sonarr.create_queue_grab_bulk", "sonarr.create_queue_grab_by_id", "sonarr.create_release",
        "sonarr.create_release_push", "sonarr.create_seasonpass", "sonarr.create_series_import",
        "sonarr.create_downloadclient_action_by_name", "sonarr.create_downloadclient_test",
        "sonarr.create_downloadclient_testall", "sonarr.create_importlist_action_by_name",
        "sonarr.create_importlist_test", "sonarr.create_importlist_testall",
        "sonarr.create_indexer_action_by_name", "sonarr.create_indexer_test",
        "sonarr.create_indexer_testall", "sonarr.create_metadata_action_by_name",
        "sonarr.create_metadata_test", "sonarr.create_metadata_testall",
        "sonarr.create_notification_action_by_name", "sonarr.create_notification_test",
        "sonarr.create_notification_testall",
    }
)

# Administrative configuration and provider changes.
ADMINISTER_TOOLS = frozenset(
    {
        "sonarr.create_customfilter", "sonarr.create_customformat", "sonarr.create_delayprofile",
        "sonarr.create_downloadclient", "sonarr.create_importlist", "sonarr.create_indexer",
        "sonarr.create_metadata", "sonarr.create_notification", "sonarr.create_qualityprofile",
        "sonarr.create_releaseprofile", "sonarr.create_remotepathmapping", "sonarr.create_rootfolder",
        "sonarr.delete_customfilter_by_id", "sonarr.delete_customformat_bulk",
        "sonarr.delete_customformat_by_id", "sonarr.delete_delayprofile_by_id",
        "sonarr.delete_downloadclient_bulk", "sonarr.delete_downloadclient_by_id",
        "sonarr.delete_importlist_bulk", "sonarr.delete_importlist_by_id", "sonarr.delete_indexer_bulk",
        "sonarr.delete_indexer_by_id", "sonarr.delete_metadata_by_id", "sonarr.delete_notification_by_id",
        "sonarr.delete_qualityprofile_by_id", "sonarr.delete_releaseprofile_by_id",
        "sonarr.delete_remotepathmapping_by_id", "sonarr.delete_rootfolder_by_id",
        "sonarr.update_config_downloadclient_by_id", "sonarr.update_config_host_by_id",
        "sonarr.update_config_importlist_by_id", "sonarr.update_config_indexer_by_id",
        "sonarr.update_config_mediamanagement_by_id", "sonarr.update_config_naming_by_id",
        "sonarr.update_config_ui_by_id", "sonarr.update_customfilter_by_id",
        "sonarr.update_customformat_bulk", "sonarr.update_customformat_by_id",
        "sonarr.update_delayprofile_by_id", "sonarr.update_delayprofile_reorder_by_id",
        "sonarr.update_downloadclient_bulk", "sonarr.update_downloadclient_by_id",
        "sonarr.update_importlist_bulk", "sonarr.update_importlist_by_id",
        "sonarr.update_indexer_bulk", "sonarr.update_indexer_by_id", "sonarr.update_metadata_by_id",
        "sonarr.update_notification_by_id", "sonarr.update_qualitydefinition_by_id",
        "sonarr.update_qualitydefinition_update", "sonarr.update_qualityprofile_by_id",
        "sonarr.update_releaseprofile_by_id", "sonarr.update_remotepathmapping_by_id",
    }
)

# Critical administrative operations. Policy outcomes remain exclusively in
# the core policy engine and are not encoded by this pack.
CRITICAL_ADMIN_TOOLS = frozenset(
    {
        "sonarr.create_system_backup_restore_by_id",
        "sonarr.create_system_backup_restore_upload",
        "sonarr.create_system_restart",
        "sonarr.create_system_shutdown",
    }
)

# Remaining reviewed state mutations.  All require approval by default.
MUTATE_TOOLS = frozenset(
    {
        "sonarr.create_autotagging", "sonarr.create_importlistexclusion", "sonarr.create_series",
        "sonarr.create_tag", "sonarr.delete_autotagging_by_id", "sonarr.delete_blocklist_bulk",
        "sonarr.delete_blocklist_by_id", "sonarr.delete_command_by_id",
        "sonarr.delete_episodefile_bulk", "sonarr.delete_episodefile_by_id",
        "sonarr.delete_importlistexclusion_bulk", "sonarr.delete_importlistexclusion_by_id",
        "sonarr.delete_queue_bulk", "sonarr.delete_queue_by_id", "sonarr.delete_series_by_id",
        "sonarr.delete_series_editor", "sonarr.delete_system_backup_by_id", "sonarr.delete_tag_by_id",
        "sonarr.update_autotagging_by_id", "sonarr.update_episode_by_id",
        "sonarr.update_episode_monitor", "sonarr.update_episodefile_bulk",
        "sonarr.update_episodefile_by_id", "sonarr.update_episodefile_editor",
        "sonarr.update_importlistexclusion_by_id", "sonarr.update_series_by_id",
        "sonarr.update_series_editor", "sonarr.update_tag_by_id",
    }
)

DESTRUCTIVE_TOOLS = frozenset(
    {
        "sonarr.create_system_backup_restore_by_id", "sonarr.create_system_backup_restore_upload",
        "sonarr.create_system_restart", "sonarr.create_system_shutdown",
        "sonarr.delete_autotagging_by_id", "sonarr.delete_blocklist_bulk", "sonarr.delete_blocklist_by_id",
        "sonarr.delete_command_by_id", "sonarr.delete_customfilter_by_id",
        "sonarr.delete_customformat_bulk", "sonarr.delete_customformat_by_id",
        "sonarr.delete_delayprofile_by_id", "sonarr.delete_downloadclient_bulk",
        "sonarr.delete_downloadclient_by_id", "sonarr.delete_episodefile_bulk",
        "sonarr.delete_episodefile_by_id", "sonarr.delete_importlist_bulk",
        "sonarr.delete_importlist_by_id", "sonarr.delete_importlistexclusion_bulk",
        "sonarr.delete_importlistexclusion_by_id", "sonarr.delete_indexer_bulk",
        "sonarr.delete_indexer_by_id", "sonarr.delete_metadata_by_id",
        "sonarr.delete_notification_by_id", "sonarr.delete_qualityprofile_by_id",
        "sonarr.delete_queue_bulk", "sonarr.delete_queue_by_id", "sonarr.delete_releaseprofile_by_id",
        "sonarr.delete_remotepathmapping_by_id", "sonarr.delete_rootfolder_by_id",
        "sonarr.delete_series_by_id", "sonarr.delete_series_editor", "sonarr.delete_system_backup_by_id",
        "sonarr.delete_tag_by_id",
    }
)


def reviewed_actions() -> dict[str, ActionReview]:
    """Return the exhaustive reviewed map, rejecting category overlap."""
    categories = {
        ActionReview("observe", "read-only"): OBSERVE_TOOLS,
        ActionReview("external-effect", "mutating"): EXTERNAL_EFFECT_TOOLS,
        ActionReview("administer", "mutating"): ADMINISTER_TOOLS,
        ActionReview("mutate", "mutating"): MUTATE_TOOLS,
        ActionReview("administer", "destructive"): CRITICAL_ADMIN_TOOLS,
    }
    result: dict[str, ActionReview] = {}
    for review, names in categories.items():
        for name in names:
            if name in result:
                raise ValueError(f"duplicate reviewed action: {name}")
            impact = "destructive" if name in DESTRUCTIVE_TOOLS else review.impact
            result[name] = ActionReview(review.action_class, impact)
    return result
