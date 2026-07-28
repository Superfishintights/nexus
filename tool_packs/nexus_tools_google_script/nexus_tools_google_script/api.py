"""Google Apps Script REST API tools."""
from __future__ import annotations

from typing import Any, Optional

from nexus.tool_registry import register_tool

from .client import coerce_json, quote_path_segment, script_request


@register_tool(
    namespace="google_script",
    tool_class="write",
    description="Create an Apps Script project, optionally bound to a parent Drive file.",
    examples=["load_tool('google_script.create_project')('Automation', parent_id='DRIVE_FILE_ID')"],
)
def create_project(title: str, *, parent_id: Optional[str] = None) -> dict:
    body = {"title": title}
    if parent_id:
        body["parentId"] = parent_id
    return script_request("POST", "projects", body=body)


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="Get Apps Script project metadata.",
    examples=["load_tool('google_script.get_project')('SCRIPT_ID')"],
)
def get_project(script_id: str) -> dict:
    return script_request("GET", f"projects/{quote_path_segment(script_id)}")


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="Get Apps Script project content files.",
    examples=["load_tool('google_script.get_content')('SCRIPT_ID', version_number=3)"],
)
def get_content(script_id: str, *, version_number: Optional[int] = None) -> dict:
    return script_request(
        "GET",
        f"projects/{quote_path_segment(script_id)}/content",
        params={"versionNumber": version_number},
    )


@register_tool(
    namespace="google_script",
    tool_class="write",
    description="Replace all Apps Script project content files.",
    examples=["load_tool('google_script.update_content')('SCRIPT_ID', files=[...])"],
)
def update_content(script_id: str, files: Any) -> dict:
    parsed_files = coerce_json(files)
    if not isinstance(parsed_files, list):
        raise ValueError("files must be a JSON array of Apps Script file objects")
    return script_request(
        "PUT",
        f"projects/{quote_path_segment(script_id)}/content",
        body={"files": parsed_files},
    )


@register_tool(
    namespace="google_script",
    tool_class="write",
    description="Create an immutable Apps Script project version.",
    examples=["load_tool('google_script.create_version')('SCRIPT_ID', description='release')"],
)
def create_version(script_id: str, *, description: Optional[str] = None) -> dict:
    body = {}
    if description is not None:
        body["description"] = description
    return script_request("POST", f"projects/{quote_path_segment(script_id)}/versions", body=body)


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="List Apps Script project versions.",
    examples=["load_tool('google_script.list_versions')('SCRIPT_ID')"],
)
def list_versions(script_id: str, *, page_size: Optional[int] = 50, page_token: Optional[str] = None) -> dict:
    return script_request(
        "GET",
        f"projects/{quote_path_segment(script_id)}/versions",
        params={"pageSize": page_size, "pageToken": page_token},
    )


@register_tool(
    namespace="google_script",
    tool_class="write",
    description="Create an Apps Script deployment for a project version.",
    examples=["load_tool('google_script.create_deployment')('SCRIPT_ID', version_number=1)"],
)
def create_deployment(
    script_id: str,
    *,
    version_number: int,
    manifest_file_name: str = "appsscript",
    description: Optional[str] = None,
) -> dict:
    config: dict[str, Any] = {
        "versionNumber": int(version_number),
        "manifestFileName": manifest_file_name,
    }
    if description is not None:
        config["description"] = description
    return script_request(
        "POST",
        f"projects/{quote_path_segment(script_id)}/deployments",
        body={"deploymentConfig": config},
    )


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="List Apps Script project deployments.",
    examples=["load_tool('google_script.list_deployments')('SCRIPT_ID')"],
)
def list_deployments(script_id: str, *, page_size: Optional[int] = 50, page_token: Optional[str] = None) -> dict:
    return script_request(
        "GET",
        f"projects/{quote_path_segment(script_id)}/deployments",
        params={"pageSize": page_size, "pageToken": page_token},
    )


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="Get one Apps Script project deployment.",
    examples=["load_tool('google_script.get_deployment')('SCRIPT_ID', 'DEPLOYMENT_ID')"],
)
def get_deployment(script_id: str, deployment_id: str) -> dict:
    return script_request(
        "GET",
        f"projects/{quote_path_segment(script_id)}/deployments/{quote_path_segment(deployment_id)}",
    )


@register_tool(
    namespace="google_script",
    tool_class="write",
    description="Update an Apps Script deployment configuration.",
    examples=["load_tool('google_script.update_deployment')('SCRIPT_ID', 'DEPLOYMENT_ID', version_number=2)"],
)
def update_deployment(
    script_id: str,
    deployment_id: str,
    *,
    version_number: int,
    manifest_file_name: str = "appsscript",
    description: Optional[str] = None,
) -> dict:
    config: dict[str, Any] = {
        "versionNumber": int(version_number),
        "manifestFileName": manifest_file_name,
    }
    if description is not None:
        config["description"] = description
    return script_request(
        "PUT",
        f"projects/{quote_path_segment(script_id)}/deployments/{quote_path_segment(deployment_id)}",
        body={"deploymentConfig": config},
    )


@register_tool(
    namespace="google_script",
    tool_class="destructive",
    description="Delete an Apps Script deployment.",
    examples=["load_tool('google_script.delete_deployment')('SCRIPT_ID', 'DEPLOYMENT_ID')"],
)
def delete_deployment(script_id: str, deployment_id: str) -> dict:
    return script_request(
        "DELETE",
        f"projects/{quote_path_segment(script_id)}/deployments/{quote_path_segment(deployment_id)}",
    )


@register_tool(
    namespace="google_script",
    tool_class="admin",
    description="Run an Apps Script function through scripts.run.",
    examples=["load_tool('google_script.run_function')('SCRIPT_ID', 'main', parameters=[])"],
)
def run_function(script_id: str, function: str, *, parameters: Any = None, dev_mode: bool = False) -> dict:
    body: dict[str, Any] = {"function": function, "devMode": bool(dev_mode)}
    parsed_parameters = coerce_json(parameters)
    if parsed_parameters is not None:
        if not isinstance(parsed_parameters, list):
            raise ValueError("parameters must be a JSON array")
        body["parameters"] = parsed_parameters
    return script_request("POST", f"scripts/{quote_path_segment(script_id)}:run", body=body)


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="List Apps Script process executions visible to the account.",
    examples=["load_tool('google_script.list_processes')(script_id='SCRIPT_ID')"],
)
def list_processes(
    *,
    script_id: Optional[str] = None,
    deployment_id: Optional[str] = None,
    function_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page_size: Optional[int] = 50,
    page_token: Optional[str] = None,
) -> dict:
    return script_request(
        "GET",
        "processes",
        params={
            "userProcessFilter.scriptId": script_id,
            "userProcessFilter.deploymentId": deployment_id,
            "userProcessFilter.functionName": function_name,
            "userProcessFilter.startTime": start_time,
            "userProcessFilter.endTime": end_time,
            "pageSize": page_size,
            "pageToken": page_token,
        },
    )


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="List Apps Script processes for one project.",
    examples=["load_tool('google_script.list_script_processes')('SCRIPT_ID')"],
)
def list_script_processes(script_id: str, *, page_size: Optional[int] = 50, page_token: Optional[str] = None) -> dict:
    return script_request(
        "GET",
        f"processes/{quote_path_segment(script_id)}",
        params={"pageSize": page_size, "pageToken": page_token},
    )


@register_tool(
    namespace="google_script",
    tool_class="read",
    description="Get Apps Script project metrics for executions or active users.",
    examples=["load_tool('google_script.get_metrics')('SCRIPT_ID', metrics_filter='executions')"],
)
def get_metrics(
    script_id: str,
    *,
    metrics_filter: str = "executions",
    granularity: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    return script_request(
        "GET",
        f"projects/{quote_path_segment(script_id)}/metrics",
        params={
            "metricsFilter": metrics_filter,
            "metricsGranularity": granularity,
            "startTime": start_time,
            "endTime": end_time,
        },
    )
