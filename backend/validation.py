"""Leitura das saídas Cisco IOS e validação da configuração solicitada."""

from __future__ import annotations

import re


DEFAULT_CISCO_VLANS = {1, 1002, 1003, 1004, 1005}


def parse_hostname(running_config: str) -> str:
    """Extrai o hostname da linha ``hostname`` da running-config."""

    match = re.search(r"^hostname\s+(\S+)", running_config, flags=re.MULTILINE)
    return match.group(1) if match else "NÃO ENCONTRADO"


def parse_vlan_brief(output: str) -> dict[int, str]:
    """Extrai ID e nome das VLANs da saída de ``show vlan brief``."""

    vlans: dict[int, str] = {}
    pattern = re.compile(r"^\s*(\d+)\s+(\S+)\s+\S+", flags=re.MULTILINE)
    for match in pattern.finditer(output):
        vlans[int(match.group(1))] = match.group(2)
    return vlans


def build_snapshot(running_config: str, vlan_brief: str) -> dict:
    """Agrupa apenas os dados necessários para comparar a configuração."""

    return {
        "hostname": parse_hostname(running_config),
        "vlans": parse_vlan_brief(vlan_brief),
    }


def validate_snapshot(hostname: str, expected_vlans: list[dict], snapshot: dict) -> list[str]:
    """Retorna divergências entre a solicitação e o estado coletado do switch."""

    issues: list[str] = []

    if snapshot["hostname"] != hostname:
        issues.append(
            f"Hostname divergente: esperado '{hostname}', encontrado '{snapshot['hostname']}'."
        )

    expected_by_id = {vlan["id"]: vlan["name"] for vlan in expected_vlans}
    for vlan_id, expected_name in expected_by_id.items():
        observed_name = snapshot["vlans"].get(vlan_id)
        if observed_name is None:
            issues.append(f"VLAN {vlan_id} ausente; esperado nome '{expected_name}'.")
        elif observed_name != expected_name:
            issues.append(
                f"VLAN {vlan_id} divergente: esperado '{expected_name}', "
                f"encontrado '{observed_name}'."
            )

    for vlan_id, observed_name in snapshot["vlans"].items():
        if vlan_id not in expected_by_id and vlan_id not in DEFAULT_CISCO_VLANS:
            issues.append(f"VLAN não solicitada encontrada: {vlan_id} ({observed_name}).")

    return issues
