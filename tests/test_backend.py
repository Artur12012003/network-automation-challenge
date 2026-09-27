"""Testes das funções que não precisam de um switch conectado."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from backend.backup import write_backup
from backend.cisco import configure_switch
from backend.config import build_configuration_commands, make_vlans, validate_configuration
from backend.validation import build_snapshot, validate_snapshot


# Dados de teste unitario; nao sao evidencias de uma execucao no laboratorio.
RUNNING_CONFIG = """version 15.2
hostname SWITCH_AUTOMATIZADO
!
vlan 10
 name VLAN_DADOS
!
vlan 20
 name VLAN_VOZ
!
vlan 50
 name VLAN_SEGURANCA
!
end
"""

VLAN_BRIEF = """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active
10   VLAN_DADOS                       active
20   VLAN_VOZ                         active
50   VLAN_SEGURANCA                   active
1002 fddi-default                     active
1003 token-ring-default               active
1004 fddinet-default                  active
1005 trnet-default                    active
"""


class BackendTests(unittest.TestCase):
    def test_connection_saves_and_collects_switch_outputs(self) -> None:
        connection = MagicMock()
        connection.send_config_set.return_value = "configured"
        connection.send_command_timing.side_effect = ["", "[confirm]", "saved"]
        connection.send_command.side_effect = [VLAN_BRIEF, RUNNING_CONFIG]
        connection_data = {
            "host": "switch.test", "port": 23, "username": "test-user",
            "password": "test-password", "secret": "",
        }
        with patch("netmiko.ConnectHandler", return_value=connection) as connect:
            result = configure_switch(connection_data, "SWITCH_AUTOMATIZADO", self.vlans)
        self.assertEqual(connect.call_args.kwargs["device_type"], "cisco_ios_telnet")
        self.assertEqual(connect.call_args.kwargs["port"], 23)
        connection.send_config_set.assert_called_once_with(
            build_configuration_commands("SWITCH_AUTOMATIZADO", self.vlans),
            exit_config_mode=False, cmd_verify=False,
        )
        self.assertEqual(connection.send_command_timing.call_args_list, [
            call("end"), call("write memory"), call("\n"),
        ])
        self.assertEqual(connection.send_command.call_args_list, [
            call("show vlan brief"), call("show running-config"),
        ])
        self.assertEqual(result["running_config"], RUNNING_CONFIG)
        self.assertEqual(result["snapshot"], build_snapshot(RUNNING_CONFIG, VLAN_BRIEF))
        connection.disconnect.assert_called_once()

    def setUp(self) -> None:
        self.vlans = make_vlans(["10", "20", "50"], ["VLAN_DADOS", "VLAN_VOZ", "VLAN_SEGURANCA"])

    def test_builds_switch_commands(self) -> None:
        commands = build_configuration_commands("SWITCH_AUTOMATIZADO", self.vlans)

        self.assertIn("vlan 10", commands)
        self.assertIn("name VLAN_DADOS", commands)
        self.assertEqual(commands[-1], "hostname SWITCH_AUTOMATIZADO")

    def test_backup_is_the_running_config_collected_from_the_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            backup = write_backup(
                "SWITCH_AUTOMATIZADO", RUNNING_CONFIG, Path(temporary_directory)
            )

            self.assertIn("SWITCH_AUTOMATIZADO", backup.name)
            self.assertEqual(backup.read_text(encoding="utf-8"), RUNNING_CONFIG)

    def test_validates_show_output_fixtures(self) -> None:
        snapshot = build_snapshot(RUNNING_CONFIG, VLAN_BRIEF)

        self.assertEqual(snapshot["hostname"], "SWITCH_AUTOMATIZADO")
        self.assertEqual(validate_snapshot("SWITCH_AUTOMATIZADO", self.vlans, snapshot), [])

    def test_reports_an_unexpected_vlan(self) -> None:
        snapshot = build_snapshot(
            RUNNING_CONFIG,
            VLAN_BRIEF + "99   VLAN_LAB                         active\n",
        )
        issues = validate_snapshot("SWITCH_AUTOMATIZADO", self.vlans, snapshot)

        self.assertEqual(issues, ["VLAN não solicitada encontrada: 99 (VLAN_LAB)."])

    def test_rejects_invalid_hostname(self) -> None:
        with self.assertRaisesRegex(ValueError, "Hostname inválido"):
            validate_configuration("switch com espaco", self.vlans)

    def test_dynamic_vlan_commands_and_boundaries(self) -> None:
        vlans = make_vlans(["2", "100", "4094"], ["FIRST", "LAB", "LAST"])
        validate_configuration("SWITCH", vlans)
        commands = build_configuration_commands("SWITCH", vlans)
        self.assertEqual(commands[:-1], [
            "vlan 2", "name FIRST", "exit",
            "vlan 100", "name LAB", "exit",
            "vlan 4094", "name LAST", "exit",
        ])
        self.assertEqual(commands[-1], "hostname SWITCH")

    def test_rejects_invalid_vlan_lists(self) -> None:
        for ids, names in [
            ([], []), (["1"], ["BAD"]), (["4095"], ["BAD"]),
            (["10", "010"], ["FIRST", "DUPLICATE"]),
            (["abc"], ["BAD"]), (["2.5"], ["BAD"]),
            ([""], ["BAD"]), (["10"], []),
            (["10"], ["bad name"]),
        ]:
            with self.subTest(ids=ids, names=names), self.assertRaises(ValueError):
                validate_configuration("SWITCH", make_vlans(ids, names))
