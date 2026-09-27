"""Validação dos dados e montagem de comandos Cisco IOS."""

from __future__ import annotations

import re


DEFAULT_VLANS = [
    {"id": 10, "name": "VLAN_DADOS"},
    {"id": 20, "name": "VLAN_VOZ"},
    {"id": 50, "name": "VLAN_SEGURANCA"},
]


class InputError(ValueError):
    """Erro de preenchimento que pode ser exibido no navegador."""


def make_vlans(vlan_id: list[str], vlan_name: list[str]) -> list[dict]:
    """Converte as listas do formulário sem descartar campos incompletos."""

    if len(vlan_id) != len(vlan_name):
        raise InputError("Informe um ID e um nome para cada VLAN.")
    vlans = []
    for raw_id, name in zip(vlan_id, vlan_name):
        try:
            identifier = int(raw_id)
        except ValueError as error:
            raise InputError("O ID da VLAN deve ser numérico.") from error
        vlans.append({"id": identifier, "name": name.strip()})
    return vlans


def validate_configuration(hostname: str, vlans: list[dict]) -> None:
    """Evita que valores inválidos sejam transformados em comandos IOS."""

    errors: list[str] = []

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,62}", hostname):
        errors.append("Hostname inválido. Use letras, números, hífen ou sublinhado.")

    if not vlans:
        errors.append("Informe pelo menos uma VLAN.")

    seen_ids: set[int] = set()
    for vlan in vlans:
        identifier = vlan["id"]
        if not 2 <= identifier <= 4094:
            errors.append("O ID da VLAN deve estar entre 2 e 4094.")
        if identifier in seen_ids:
            errors.append(f"ID de VLAN duplicado: {identifier}.")
        seen_ids.add(identifier)
        name = vlan["name"]
        if not re.fullmatch(r"[\w.-]{1,32}", name, flags=re.UNICODE):
            errors.append(
                f"VLAN {vlan['id']}: informe um nome de até 32 caracteres, sem espaços."
            )

    if errors:
        raise InputError(" ".join(errors))


def build_configuration_commands(hostname: str, vlans: list[dict]) -> list[str]:
    """Comandos de configuração usados pelo Netmiko dentro do modo config."""

    commands: list[str] = []
    for vlan in vlans:
        commands.extend([f"vlan {vlan['id']}", f"name {vlan['name']}", "exit"])

    # O hostname é alterado por último. Assim a conexão com o switch pode atualizar o prompt
    # antes de salvar e coletar as saídas reais do equipamento.
    commands.append(f"hostname {hostname}")
    return commands
