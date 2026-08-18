# Active Nexus Tool Inventory

This repository contains the source for every tool pack configured in Jay's
local Nexus deployment on 2026-08-18. A clean scan of the published source
reported 1,659 canonical tools across 27 namespaces. The long-running live
catalog reported 1,653 tools; the six-tool difference is in the local Tautulli
pack and will appear after that runtime catalog is refreshed.

`nexus_tools_google_common` is a shared support package and does not register
its own namespace.

| Namespace | Tools | Package |
| --- | ---: | --- |
| `agent_memory` | 8 | `nexus_tools_agent_memory` |
| `audiobookshelf` | 60 | `nexus_tools_audiobookshelf` |
| `bazarr` | 79 | `nexus_tools_bazarr` |
| `google_calendar` | 42 | `nexus_tools_google_calendar` |
| `google_docs` | 16 | `nexus_tools_google_docs` |
| `google_drive` | 65 | `nexus_tools_google_drive` |
| `google_forms` | 26 | `nexus_tools_google_forms` |
| `google_gmail` | 52 | `nexus_tools_google_gmail` |
| `google_people` | 24 | `nexus_tools_google_people` |
| `google_script` | 15 | `nexus_tools_google_script` |
| `google_sheets` | 44 | `nexus_tools_google_sheets` |
| `google_slides` | 57 | `nexus_tools_google_slides` |
| `google_tasks` | 14 | `nexus_tools_google_tasks` |
| `jira` | 1 | `nexus_tools_jira` |
| `n8n` | 60 | `nexus_tools_n8n` |
| `nzbget` | 41 | `nexus_tools_nzbget` |
| `playtomic` | 3 | `nexus_tools_playtomic` |
| `portainer` | 13 | `nexus_tools_portainer` |
| `prowlarr` | 129 | `nexus_tools_prowlarr` |
| `qbittorrent` | 91 | `nexus_tools_qbittorrent` |
| `radarr` | 228 | `nexus_tools_radarr` |
| `sabnzbd` | 60 | `nexus_tools_sabnzbd` |
| `sonarr` | 222 | `nexus_tools_sonarr` |
| `starling` | 123 | `nexus_tools_starling` |
| `tautulli` | 133 | `nexus_tools_tautulli` |
| `vaultwarden` | 33 | `nexus_tools_vaultwarden` |
| `waha` | 20 | `nexus_tools_waha` |

The active runtime loads the 27 package roots through `NEXUS_TOOL_PACKAGES`.
Google service packs automatically load `nexus_tools_google_common`.
