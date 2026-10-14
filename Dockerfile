# syntax=docker/dockerfile:1.4
FROM node:22-bookworm-slim AS bitwarden_cli
RUN npm install --global @bitwarden/cli@2025.12.1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NEXUS_HTTP_HOST=0.0.0.0 NEXUS_HTTP_PORT=8000 NEXUS_HTTP_PATH=/mcp
ENV NEXUS_TOOL_PACKAGES=nexus_tools_agent_memory,nexus_tools_audiobookshelf,nexus_tools_bazarr,nexus_tools_jira,nexus_tools_n8n,nexus_tools_nzbget,nexus_tools_playtomic,nexus_tools_portainer,nexus_tools_prowlarr,nexus_tools_qbittorrent,nexus_tools_radarr,nexus_tools_sabnzbd,nexus_tools_sonarr,nexus_tools_starling,nexus_tools_tautulli,nexus_tools_vaultwarden,nexus_tools_waha,nexus_tools_google_calendar,nexus_tools_google_docs,nexus_tools_google_drive,nexus_tools_google_forms,nexus_tools_google_gmail,nexus_tools_google_people,nexus_tools_google_script,nexus_tools_google_sheets,nexus_tools_google_slides,nexus_tools_google_tasks,nexus_tools_vikunja,nexus_tools_ticktick,nexus_tools_chaptarr
WORKDIR /app
COPY --from=bitwarden_cli /usr/local/bin/node /usr/local/bin/node
COPY --from=bitwarden_cli /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/@bitwarden/cli/build/bw.js /usr/local/bin/bw
COPY nexus ./nexus
COPY tool_packs ./tool_packs
COPY requirements-runtime.txt ./requirements-runtime.txt
RUN pip install --no-cache-dir -c requirements-runtime.txt ./nexus ./tool_packs/nexus_tools_* \
    && python -m nexus.selftest \
    && useradd --create-home --shell /usr/sbin/nologin nexus \
    && chown -R nexus:nexus /app
USER nexus
EXPOSE 8000
CMD ["python", "-m", "nexus.http_server"]
