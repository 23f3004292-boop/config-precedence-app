import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS: dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ENV_NAME = os.getenv("APP_ENV", "development")
YAML_PATH = BASE_DIR / f"config.{ENV_NAME}.yaml"

app = FastAPI(title="12-Factor Config Precedence API")

# Allow browser-based graders/pages to call the API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}

def coerce(key: str, value: Any) -> Any:
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)

def merge_config() -> dict[str, Any]:
    # Layer 1: hardcoded defaults
    config = dict(DEFAULTS)

    # Layer 2: environment-specific YAML
    if YAML_PATH.exists():
        with YAML_PATH.open("r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        for key in DEFAULTS:
            if key in yaml_config:
                config[key] = coerce(key, yaml_config[key])

    # Layer 3: .env file (with assignment-specific aliases)
    env_file = dotenv_values(BASE_DIR / ".env")
    env_mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }
    for env_name, key in env_mapping.items():
        value = env_file.get(env_name)
        if value is not None:
            config[key] = coerce(key, value)

    # Layer 4: real OS environment variables override .env
    for env_name, key in env_mapping.items():
        value = os.environ.get(env_name)
        if value is not None:
            config[key] = coerce(key, value)

    return config

@app.get("/")
def root():
    return {"service": "effective-config", "status": "ok"}

@app.get("/effective-config")
def effective_config(set_values: list[str] | None = Query(default=None, alias="set")):
    config = merge_config()

    # Layer 5: CLI-style query overrides. Multiple ?set=key=value values are supported.
    allowed_keys = set(config.keys())
    for item in set_values or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        if key in allowed_keys:
            config[key] = coerce(key, value.strip())

    # Never reveal the actual secret, including if the caller overrides it.
    config["api_key"] = "*****"
    return config
