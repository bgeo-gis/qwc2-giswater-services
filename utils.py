from typing import Optional, List
from datetime import date

from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine

import os
import logging

app = None
api = None
tenant_handler = None

def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("giswater", app.logger)
    return config_handler.tenant_config(tenant)

def get_db(theme: str = None) -> DatabaseEngine:
    print(f"DB URL: {get_config().get('db_url')}")
    logging.basicConfig
    logging.info(f"DB URL: {get_config().get('db_url')}")
    db_url = None
    if theme is not None:
        db_url = get_db_url_from_theme(theme)
    if not db_url:
        db_url = get_config().get("db_url")

    return DatabaseEngine().db_engine(db_url)

def get_schema_from_theme(theme: str, config: RuntimeConfig) -> Optional[str]:
    themes = get_config().get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("schema")
    return None

def get_db_url_from_theme(theme: str) -> Optional[str]:
    themes = get_config().get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("db_url")
    return None

def get_db_layers(theme: str) -> List[str]:
    db_layers = []
    theme = get_config().get("themes").get(theme)
    if theme is not None:
        db_layers = theme.get("layers")
    return db_layers

def parse_layers(request_layers: str, config: RuntimeConfig, theme: str) -> List[str]:
    layers = []
    db_layers = []
    theme = config.get("themes").get(theme)
    if theme is not None:
        db_layers = theme.get("layers")

    for l in request_layers.split(','):
        if l in db_layers:
            layers.append(db_layers[l])
    return layers


# Create log pointer
def create_log(class_name):
    print(f"Tenant_name -> {tenant_handler.tenant()}")
    today = date.today()
    today = today.strftime("%Y%m%d")

    # Directory where log file is saved, changes location depending on what tenant is used
    tenant_directory = f"/var/log/qwc2-giswater-services/{tenant_handler.tenant()}"
    if not os.path.exists(tenant_directory):
        os.makedirs(tenant_directory)
    
    # Check if today's direcotry is created
    today_directory = f"{tenant_directory}/{today}"
    if not os.path.exists(today_directory):
        os.makedirs(today_directory)
    
    service_name = os.getcwd().split(os.sep)[-1]
    # Select file name for the log
    log_file = f"{service_name}_{today}.log"

    fileh = logging.FileHandler(f"{today_directory}/{log_file}", "a", encoding="utf-8")
    # Declares how log info is added to the file
    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s", datefmt = "%d/%m/%y %H:%M:%S")
    fileh.setFormatter(formatter)

    # Removes previous handlers on root Logger
    remove_handlers()
    # Gets root Logger and add handler
    log = logging.getLogger()
    log.addHandler(fileh)
    log.setLevel(logging.DEBUG)
    log.info(f" Executing class {class_name}")
    return log

# Removes previous handlers on root Logger
def remove_handlers():
    log = logging.getLogger()
    for hdlr in log.handlers[:]:
        log.removeHandler(hdlr)
