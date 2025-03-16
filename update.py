import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import yaml
import requests
from pathlib import Path


@dataclass
class UpstreamRepo:
    repo: str
    commit: str  # Changed to str since commits are typically hex strings
    dest: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Set 'dest' to repo name if not provided."""
        if self.dest is None:
            self.dest = self.repo


@dataclass
class Config:
    upstreams: List[UpstreamRepo]


def ensure_folder_exists(folder_path: str) -> Path:
    """
    Check if a folder exists; if not, create it.

    Args:
        folder_path: Path to the folder to create

    Returns:
        Path object of the created/existing folder
    """
    path = Path(folder_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config(file_path: str) -> Config:
    """
    Loads YAML configuration and converts it into a Config object.

    Args:
        file_path: Path to the YAML config file

    Returns:
        Config object containing upstream repositories

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        upstream_list = [UpstreamRepo(**entry) for entry in data.get("upstreams", [])]
        return Config(upstreams=upstream_list)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {file_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")


def download_file(repo: str, commit: str, file_name: str = "action.yml") -> Dict[str, Any]:
    """
    Downloads a file from a GitHub repository.

    Args:
        repo: GitHub repository path
        commit: Commit hash or reference
        file_name: Name of the file to download

    Returns:
        Parsed YAML content as dictionary

    Raises:
        requests.exceptions.RequestException: If download fails
    """
    raw_url = f"https://raw.githubusercontent.com/{repo}/{commit}/{file_name}"

    print(f"Fetching {raw_url}")
    response = requests.get(raw_url, timeout=30)
    response.raise_for_status()

    return yaml.safe_load(response.text)


def extract_action_data(upstream_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and transforms action configuration data.

    Args:
        upstream_config: Raw action configuration

    Returns:
        Processed action configuration
    """
    return {
        "name": upstream_config.get("name", ""),
        "description": upstream_config.get("description", ""),
        "inputs": upstream_config.get("inputs", {}),
    }


def create_composite_runs(repo: str, commit: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates the composite runs configuration.

    Args:
        repo: GitHub repository path
        commit: Commit hash
        inputs: Input parameters

    Returns:
        Composite runs configuration
    """
    with_items = {
        input_name: "${{inputs.%s}}" % input_name
        for input_name in inputs.keys()
    }

    return {
        "using": "composite",
        "steps": [{
            "uses": f"{repo}@{commit}",
            "id": "upstream",
            "with": with_items,
        }]
    }


def create_outputs_config(upstream_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates the outputs configuration.

    Args:
        upstream_outputs: Original outputs configuration

    Returns:
        Processed outputs configuration
    """
    return {
        output: {"value": f"${{{{ steps.upstream.outputs.{output} }}}}"}
        for output in upstream_outputs.keys()
    }


def create_local_composite_action(upstream: UpstreamRepo) -> None:
    """
    Creates a local composite action from an upstream repository.

    Args:
        upstream: UpstreamRepo configuration
    """
    try:
        upstream_action_config = download_file(upstream.repo, upstream.commit)

        # Extract and process data
        action_data = extract_action_data(upstream_action_config)
        action_data["runs"] = create_composite_runs(
            upstream.repo,
            upstream.commit,
            action_data["inputs"]
        )
        action_data["outputs"] = create_outputs_config(
            upstream_action_config.get("outputs", {})
        )

        # Save the composite action
        dest_path = ensure_folder_exists(upstream.dest)
        output_file = dest_path / "action.yml"

        print(f"Saving composite action config to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as yaml_file:
            yaml.dump(action_data, yaml_file, default_flow_style=False, allow_unicode=True)

    except (requests.exceptions.RequestException, yaml.YAMLError) as e:
        print(f"Error processing {upstream.repo}: {e}")


def main() -> None:
    """Main entry point for the script."""
    CONFIG_FILE = "config.yml"
    try:
        config_data = load_config(CONFIG_FILE)
        for entry in config_data.upstreams:
            create_local_composite_action(entry)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
