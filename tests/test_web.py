"""Teste básico do frontend Flask."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontend import app as web_app


class WebTests(unittest.TestCase):
    def setUp(self) -> None:
        web_app.app.config.update(TESTING=True)
        self.client = web_app.app.test_client()

    def test_page_opens(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Configura", response.data)

    def test_apply_dynamic_vlans(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(web_app, "PROJECT_DIR", Path(directory)), patch.object(
                web_app, "configure_switch", return_value={
                    "snapshot": {"hostname": "SWITCH", "vlans": {100: "LAB"}},
                    "running_config": "hostname SWITCH\nend\n",
                    "configuration_output": "configured",
                    "save_output": "saved",
                }
            ) as configure:
                response = self.client.post("/", data={
                    "action": "apply", "hostname": "SWITCH",
                    "vlan_id": ["100"], "vlan_name": ["LAB"],
                    "host": "switch.test", "username": "admin", "password": "password",
                })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(configure.call_args.args[0]["port"], 23)
            self.assertEqual(configure.call_args.args[2], [{"id": 100, "name": "LAB"}])
            self.assertIn("Configuração validada", response.get_data(as_text=True))
            backups = list((Path(directory) / "backups").glob("*.txt"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "hostname SWITCH\nend\n")

    def test_invalid_vlans_preserved_without_connection(self) -> None:
        with patch.object(web_app, "configure_switch") as configure:
            response = self.client.post("/", data={
                "action": "apply", "vlan_id": ["100", "100"],
                "vlan_name": ["LAB", "DUPLICATE"],
            })
        configure.assert_not_called()
        page = response.get_data(as_text=True)
        self.assertIn("duplicado", page)
        self.assertIn('value="DUPLICATE"', page)

    def test_interface_has_only_apply_and_connection_flow(self) -> None:
        page = self.client.get("/").get_data(as_text=True)
        for text in ("Adicionar VLAN", "Remover", "Aplicar configuração", "Dados de conexão",
                     "VLAN_DADOS", "VLAN_VOZ", "VLAN_SEGURANCA"):
            self.assertIn(text, page)
        self.assertEqual(page.count('type="submit"'), 1)

    def test_empty_vlans_are_rejected_before_connection(self) -> None:
        with patch.object(web_app, "configure_switch") as configure:
            response = self.client.post("/", data={"action": "apply"})
        configure.assert_not_called()
        self.assertIn("Informe pelo menos uma VLAN.", response.get_data(as_text=True))

    def test_unknown_action_is_rejected(self) -> None:
        with patch.object(web_app, "configure_switch") as configure:
            response = self.client.post("/", data={
                "action": "unknown", "vlan_id": ["10"], "vlan_name": ["DATA"],
            })
        configure.assert_not_called()
        self.assertIn('role="alert"', response.get_data(as_text=True))
