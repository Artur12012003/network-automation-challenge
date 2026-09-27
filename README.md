# Network Automation Challenge

Projeto de automação de redes dividido em duas partes:

- Parte 1: configuração de switch Cisco.
- Parte 2: planejamento de VPN IPSec entre FortiGate e Palo Alto.

## Parte 1 - Switch Cisco

Aplicação web em Python para configurar VLANs e hostname em um switch Cisco.

O script também executa o salvamento da configuração, cria backup da running-config e valida o resultado.

### VLANs do teste

| VLAN | Nome |
| --- | --- |
| 10 | VLAN_DADOS |
| 20 | VLAN_VOZ |
| 50 | VLAN_SEGURANCA |


### Como executar

No PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py run.py
```

Depois, acesse:

http://127.0.0.1:5000

### Uso

Preencha o hostname, as VLANs e os dados de conexão do switch. Em seguida, clique em **Aplicar configuração**.

O teste foi realizado no Cisco CML DevNet Sandbox, utilizando Telnet na porta 23. Para um switch Cisco real, a aplicação aceita SSH na porta 22.

### Evidências

- [Formulário](evidence/01-frontend-formulario.png)
- [Validação no frontend](evidence/02-frontend-validacao-sucesso.png)
- [VLANs e hostname na CLI](evidence/03-cli-vlans-hostname.png)
- [Backup local](evidence/04-backup-local.png)
- [Alerta de validação](evidence/05-alerta-validacao.png)

## Parte 2 - VPN IPSec

[Plano de automação da VPN IPSec](docs/PLANO_VPN_IPSEC.md)