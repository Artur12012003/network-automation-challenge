# Automação de switch Cisco

## Objetivo

Configurar VLANs e hostname de um switch Cisco por um formulário web, salvar a configuração, criar um backup local e conferir o resultado.

O projeto foi testado no Cisco CML DevNet Sandbox, em um switch Cisco IOL L2, usando Netmiko por Telnet na porta 23. A aplicação também aceita a porta 22 para conexão SSH em switches Cisco reais.

## Requisitos

- Windows com Python 3.10 ou superior e pip.
- Flask e Netmiko, instalados pelo arquivo `requirements.txt`.
- Acesso de rede ao switch, com endereço, porta e credenciais que permitam configurar e salvar.

## Instalação e execução no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py run.py
```

Se o PowerShell bloquear a ativação, use o Python do ambiente diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000). Para encerrar, pressione `Ctrl+C` no terminal. Reinicie a aplicação depois de alterar o código ou os templates.

## Como usar

Informe o hostname, confira as VLANs e preencha os dados de conexão. No laboratório CML usado, a porta é 23. Depois, clique em **Aplicar configuração**.

O formulário começa com:

| ID | Nome |
| --- | --- |
| 10 | VLAN_DADOS |
| 20 | VLAN_VOZ |
| 50 | VLAN_SEGURANCA |

O requisito original cita `VLAN_SEGURANÇA`, mas o CML IOL L2 usado no teste não aceitou o caractere Ç na CLI. Por isso, o teste funcional usou `VLAN_SEGURANCA`.

Os botões **Adicionar VLAN** e **Remover** alteram as linhas do formulário. É necessário informar pelo menos uma VLAN, com IDs únicos entre 2 e 4094. Remover uma linha não exclui uma VLAN já existente no switch.

## Fluxo

Formulário → validação dos campos → conexão → comandos Cisco → `write memory` → `show running-config` / `show vlan brief` → backup → validação do resultado.

O backend envia as VLANs e altera o hostname por último. O comando `write memory` salva a configuração para que ela seja mantida após reiniciar o switch.

O backup contém a saída real de `show running-config`. Os arquivos são criados localmente em `backups/`, com hostname e data/hora no nome, e não são publicados; essa pasta está no `.gitignore`.

A validação compara o hostname de `show running-config` e as VLANs de `show vlan brief` com o que foi solicitado. O frontend mostra o resultado e os alertas de divergência.

## Evidências

- [Formulário com hostname e VLANs](evidence/01-frontend-formulario.png)
- [Configuração validada no frontend](evidence/02-frontend-validacao-sucesso.png)
- [VLANs e hostname na CLI do switch](evidence/03-cli-vlans-hostname.png)
- [Arquivos de backup local](evidence/04-backup-local.png)
- [Alerta de divergências na validação](evidence/05-alerta-validacao.png)

A captura do formulário mostra a porta 22 preenchida; o teste funcional no CML utilizou Telnet na porta 23.
