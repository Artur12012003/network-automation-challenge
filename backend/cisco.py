"""Conexão com o switch Cisco IOS/IOS XE usando Netmiko."""

from __future__ import annotations

from .config import build_configuration_commands
from .validation import build_snapshot


def configure_switch(connection_data: dict, hostname: str, vlans: list[dict]) -> dict:
    """Configura, salva e coleta a configuração real de um switch Cisco."""

    try:
        from netmiko import ConnectHandler
    except ImportError as error:
        raise RuntimeError("Instale as dependências com 'pip install -r requirements.txt'.") from error

    connection = None
    try:
        connection = ConnectHandler(
            device_type="cisco_ios_telnet" if connection_data["port"] == 23 else "cisco_ios",
            host=connection_data["host"],
            port=connection_data["port"],
            username=connection_data["username"],
            password=connection_data["password"],
            secret=connection_data["secret"],
            encoding="latin-1",
            conn_timeout=15,
            banner_timeout=15,
            auth_timeout=15,
        )
        if connection_data["secret"]:
            connection.enable()

        # O hostname é o último comando. Mantemos a sessão no modo config e
        # encerramos com send_command_timing para aceitar a troca de prompt.
        configuration_output = connection.send_config_set(
            build_configuration_commands(hostname, vlans),
            exit_config_mode=False,
            cmd_verify=False,
        )
        end_output = connection.send_command_timing("end")
        connection.set_base_prompt()

        save_output = connection.send_command_timing("write memory")
        if "confirm" in save_output.lower() or "destination filename" in save_output.lower():
            save_output += connection.send_command_timing("\n")

        vlan_brief = connection.send_command("show vlan brief")
        running_config = connection.send_command("show running-config")
        return {
            "configuration_output": configuration_output + end_output,
            "save_output": save_output,
            "running_config": running_config,
            "vlan_brief": vlan_brief,
            "snapshot": build_snapshot(running_config, vlan_brief),
        }
    except Exception as error:
        raise RuntimeError(f"Falha na conexão: {error}") from error
    finally:
        if connection is not None:
            try:
                connection.disconnect()
            except Exception:
                pass
