"""Frontend Flask do desafio de automação Cisco."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template, request

from backend.backup import write_backup
from backend.cisco import configure_switch
from backend.config import (
    DEFAULT_VLANS,
    InputError,
    make_vlans,
    validate_configuration,
)
from backend.validation import validate_snapshot


PROJECT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR / "static"),
)


def default_form() -> dict:
    """Valores iniciais usados na tela."""

    return {
        "hostname": "SWITCH_AUTOMATIZADO",
        "vlan_id": [str(vlan["id"]) for vlan in DEFAULT_VLANS],
        "vlan_name": [vlan["name"] for vlan in DEFAULT_VLANS],
        "host": "",
        "port": "23",
        "username": "",
    }


def form_values() -> dict:
    """Lê campos sem devolver senha ao navegador."""

    form = default_form()
    for field in ("hostname", "host", "port", "username"):
        form[field] = request.form.get(field, form[field]).strip()
    form["vlan_id"] = request.form.getlist("vlan_id")
    form["vlan_name"] = request.form.getlist("vlan_name")
    return form


def read_configuration(form: dict) -> tuple[str, list[dict]]:
    """Converte o formulário em hostname e VLANs validados."""

    hostname = form["hostname"]
    vlans = make_vlans(form["vlan_id"], form["vlan_name"])
    validate_configuration(hostname, vlans)
    return hostname, vlans


def read_connection_data(form: dict) -> dict:
    """Lê os dados para a conexão com o switch."""

    try:
        port = int(form["port"])
    except ValueError as error:
        raise InputError("A porta deve ser numérica.") from error

    password = request.form.get("password", "")
    secret = request.form.get("secret", "")
    if not form["host"] or not form["username"] or not password:
        raise InputError("Para conectar, informe IP/DNS, usuário e senha.")
    if not 1 <= port <= 65535:
        raise InputError("A porta deve estar entre 1 e 65535.")

    return {
        "host": form["host"],
        "port": port,
        "username": form["username"],
        "password": password,
        "secret": secret,
    }


def backup_path(backup_file: Path) -> str:
    """Mostra um caminho curto quando o backup está dentro do projeto."""

    return str(backup_file.relative_to(PROJECT_DIR))


def result_from_snapshot(source: str, hostname: str, vlans: list[dict], snapshot: dict, running_config: str) -> dict:
    """Gera backup e resultado de validação usando dados reais coletados."""

    backup_file = write_backup(snapshot["hostname"], running_config, PROJECT_DIR / "backups")
    issues = validate_snapshot(hostname, vlans, snapshot)
    return {
        "kind": "validation",
        "source": source,
        "snapshot": snapshot,
        "issues": issues,
        "validation_ok": not issues,
        "backup_relative": backup_path(backup_file),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    """Mostra a tela e aplica a configuração no switch."""

    form = default_form()
    result = None
    errors: list[str] = []

    if request.method == "POST":
        form = form_values()
        try:
            hostname, vlans = read_configuration(form)
            action = request.form.get("action")

            if action == "apply":
                switch_result = configure_switch(read_connection_data(form), hostname, vlans)
                result = result_from_snapshot(
                    "Conexão com o switch", hostname, vlans, switch_result["snapshot"], switch_result["running_config"]
                )
                result["configuration_output"] = switch_result["configuration_output"]
                result["save_output"] = switch_result["save_output"]
            else:
                raise InputError("Escolha uma ação para continuar.")
        except (InputError, RuntimeError) as error:
            errors.append(str(error))

    return render_template("index.html", form=form, result=result, errors=errors)


@app.get("/health")
def health():
    return {"status": "ok"}
