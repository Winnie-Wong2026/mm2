from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from .base import BaseStrategy
from .config import StrategyConfig


class StrategyRegistry:
    def __init__(self) -> None:
        self._classes: Dict[str, Type[BaseStrategy]] = {}
        self._configs: Dict[str, StrategyConfig] = {}

    def register(self, strategy_class: Type[BaseStrategy], config: StrategyConfig) -> None:
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError("strategy_class must inherit from BaseStrategy")
        if config.strategy_id in self._classes:
            raise ValueError(f"Strategy already registered: {config.strategy_id}")
        self._classes[config.strategy_id] = strategy_class
        self._configs[config.strategy_id] = config

    def discover(self, root: str) -> List[str]:
        root_path = Path(root)
        if not root_path.exists():
            return []

        registered: List[str] = []
        for config_path in sorted(root_path.rglob("strategy.yaml")):
            config = load_strategy_config(config_path)
            if not config.enabled:
                continue
            strategy_class = import_strategy_class(config)
            self.register(strategy_class, config)
            registered.append(config.strategy_id)
        return registered

    def create(self, strategy_id: str) -> BaseStrategy:
        if strategy_id not in self._classes:
            raise KeyError(f"Unknown strategy_id: {strategy_id}")
        return self._classes[strategy_id](self._configs[strategy_id])

    def get_config(self, strategy_id: str) -> StrategyConfig:
        if strategy_id not in self._configs:
            raise KeyError(f"Unknown strategy_id: {strategy_id}")
        return self._configs[strategy_id]

    def list_strategy_ids(self) -> List[str]:
        return sorted(self._classes)

    def list_configs(self) -> List[StrategyConfig]:
        return [self._configs[strategy_id] for strategy_id in self.list_strategy_ids()]


def load_strategy_config(config_path: Path) -> StrategyConfig:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        data = load_simple_yaml(config_path)
    else:
        with config_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

    return StrategyConfig.from_mapping(data)


def import_strategy_class(config: StrategyConfig) -> Type[BaseStrategy]:
    module = importlib.import_module(config.entrypoint_module)
    strategy_class = getattr(module, config.entrypoint_class)
    if not issubclass(strategy_class, BaseStrategy):
        raise TypeError(
            f"{config.entrypoint_module}.{config.entrypoint_class} must inherit from BaseStrategy"
        )
    return strategy_class


def build_registry(strategy_roots: Optional[Iterable[str]] = None) -> StrategyRegistry:
    registry = StrategyRegistry()
    roots = list(strategy_roots or [str(Path(__file__).parent / "examples")])
    for root in roots:
        registry.discover(root)
    return registry


def load_simple_yaml(config_path: Path) -> Dict[str, Any]:
    lines = []
    with config_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            lines.append((indent, stripped))

    data, index = _parse_mapping(lines, 0, 0)
    if index != len(lines):
        raise ValueError(f"Could not parse full yaml file: {config_path}")
    return data


def _parse_mapping(
    lines: List[Tuple[int, str]],
    index: int,
    indent: int,
) -> Tuple[Dict[str, Any], int]:
    result: Dict[str, Any] = {}
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected indentation near: {text}")
        if text.startswith("- "):
            break
        key, raw_value = _split_key_value(text)
        if raw_value:
            result[key] = _parse_scalar(raw_value)
            index += 1
            continue

        if index + 1 >= len(lines) or lines[index + 1][0] <= indent:
            result[key] = {}
            index += 1
            continue

        next_indent, next_text = lines[index + 1]
        if next_text.startswith("- "):
            result[key], index = _parse_list(lines, index + 1, next_indent)
        else:
            result[key], index = _parse_mapping(lines, index + 1, next_indent)
    return result, index


def _parse_list(
    lines: List[Tuple[int, str]],
    index: int,
    indent: int,
) -> Tuple[List[Any], int]:
    result: List[Any] = []
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected list indentation near: {text}")
        if not text.startswith("- "):
            break
        result.append(_parse_scalar(text[2:].strip()))
        index += 1
    return result, index


def _split_key_value(text: str) -> Tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"Invalid yaml line: {text}")
    key, raw_value = text.split(":", 1)
    return key.strip(), raw_value.strip()


def _parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
