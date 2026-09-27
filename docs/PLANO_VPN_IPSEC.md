# Plano de automação de VPN IPSec - Parte 2

## Contexto

Nesta etapa eu montei um plano de como automatizaria uma VPN IPSec entre um FortiGate e um Palo Alto.

Como esta etapa tem foco no planejamento, não foi realizada uma simulação funcional da VPN.

## Decisões adotadas

Para o exemplo, escolhi IKEv2 com AES-256, SHA-256 e DH Group 14. A ideia é usar a mesma proposta nos dois lados para evitar problema de negociação.

Os IPs WAN abaixo são apenas exemplos de documentação. Em um cenário real, seriam substituídos pelos IPs públicos dos firewalls.

## Parâmetros da VPN

| Item | FortiGate | Palo Alto |
| --- | --- | --- |
| IP WAN | 203.0.113.10 | 198.51.100.10 |
| Rede local | 10.10.10.0/24 | 10.20.20.0/24 |
| IP do túnel | 169.255.1.1/30 | 169.255.1.2/30 |

| Configuração | Valor |
| --- | --- |
| IKE | IKEv2 |
| Autenticação | Chave pré-compartilhada |
| Phase 1 | AES-256, SHA-256, DH Group 14, tempo de vida 28800 segundos |
| Phase 2 | ESP AES-256, SHA-256, PFS Group 14, tempo de vida 3600 segundos |

A chave pré-compartilhada deve ser igual nos dois lados e não deve ser salva no Git.

## Ferramentas

A automação pode ser feita em Python utilizando requisições HTTPS para as APIs dos firewalls.

- FortiGate: API REST do FortiOS.
- Palo Alto: API REST do PAN-OS.
- Palo Alto: XML API para commit, quando necessário.

Também seria possível usar SSH com Netmiko, mas a API é mais indicada para uma automação desse tipo.

## Etapas no FortiGate

1. Validar os dados recebidos.
2. Criar objetos para as redes 10.10.10.0/24 e 10.20.20.0/24.
3. Criar a Phase 1 com IKEv2, IP WAN do Palo Alto e chave pré-compartilhada.
4. Criar a Phase 2 com as propostas e redes definidas.
5. Configurar a interface do túnel com 169.255.1.1/30.
6. Criar rota para 10.20.20.0/24.
7. Criar políticas permitindo tráfego entre a LAN e a VPN, sem NAT.

## Etapas no Palo Alto

1. Criar objetos para as redes 10.20.20.0/24 e 10.10.10.0/24.
2. Criar o perfil IKE com os parâmetros da Phase 1.
3. Criar o IKE Gateway apontando para o FortiGate.
4. Criar o perfil IPSec com os parâmetros da Phase 2.
5. Criar a interface de túnel com 169.255.1.2/30.
6. Associar a interface à zona VPN e ao virtual router.
7. Criar rota para 10.10.10.0/24.
8. Criar regras de segurança entre a LAN e a VPN, sem NAT.
9. Executar o commit da configuração.

## Pontos de atenção

- As propostas de Phase 1 e Phase 2 devem ser iguais nos dois lados.
- A rede local de um firewall será a rede remota do outro.
- Devem existir rotas de ida e volta.
- As políticas de firewall devem permitir o tráfego desejado.
- É necessário validar regras de NAT existentes.
- Em caso de NAT entre os peers, deve ser utilizado NAT-T.

## Validação e alertas

Após a configuração, a automação deve verificar:

- Estado da Phase 1 e da Phase 2.
- IPs configurados nas interfaces de túnel.
- Rotas para as redes remotas.
- Políticas de firewall.
- Contadores de tráfego no túnel.
- Ping entre um host da rede 10.10.10.0/24 e outro da rede 10.20.20.0/24, caso exista ambiente para teste.

Como exemplo de consulta, no FortiGate podem ser usados os comandos diagnose vpn ike gateway list e diagnose vpn tunnel list. No Palo Alto, podem ser usados show vpn ike-sa e show vpn ipsec-sa.

Em uma automação por API, o script consultaria as informações equivalentes retornadas pelos dois firewalls antes de informar sucesso.

Em caso de falha, o script deve informar o firewall, a etapa que apresentou erro e a mensagem retornada pela API.

Exemplos de alerta:

- Falha de conexão com a API.
- Erro na criação de objeto, rota ou política.
- Erro no commit do Palo Alto.
- Phase 1 ou Phase 2 inativa.
- Túnel ativo, mas sem tráfego entre as redes.