"""Configuration loader for Peru frozen fruit export analysis pipeline.

This module provides utilities to load and access configuration from config.yaml,
with path resolution for relative paths.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load pipeline configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses config.yaml in current directory.

    Returns:
        Dict containing configuration

    Raises:
        ValueError: If required configuration keys are missing
        FileNotFoundError: If config file doesn't exist
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required keys
    required = ['pipeline']
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    return config


def get_input_path(config: Dict, key: str, base_dir: Optional[Path] = None) -> Path:
    """Get input file path from config, resolving relative paths.

    Args:
        config: Configuration dictionary
        key: Key name in pipeline.inputs section
        base_dir: Base directory for relative path resolution. If None, uses config file directory.

    Returns:
        Resolved absolute Path object

    Raises:
        KeyError: If input path key not found in config
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    path_str = config['pipeline']['inputs'].get(key)
    if not path_str:
        raise KeyError(f"Input path '{key}' not found in config")

    path = Path(path_str)
    if not path.is_absolute():
        path = base_dir / path

    return path.resolve()


def get_output_path(config: Dict, key: str, base_dir: Optional[Path] = None) -> Path:
    """Get output file path from config, resolving relative paths.

    Args:
        config: Configuration dictionary
        key: Key name in pipeline.outputs section
        base_dir: Base directory for relative path resolution. If None, uses config file directory.

    Returns:
        Resolved absolute Path object

    Raises:
        KeyError: If output path key not found in config
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    path_str = config['pipeline']['outputs'].get(key)
    if not path_str:
        raise KeyError(f"Output path '{key}' not found in config")

    path = Path(path_str)
    if not path.is_absolute():
        path = base_dir / path

    return path.resolve()


def get_processing_param(config: Dict, key: str, default: Any = None) -> Any:
    """Get processing parameter from config.

    Args:
        config: Configuration dictionary
        key: Key name in pipeline.processing section
        default: Default value if key not found

    Returns:
        Parameter value or default
    """
    return config.get('pipeline', {}).get('processing', {}).get(key, default)
