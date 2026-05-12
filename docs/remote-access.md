# Conectando a um Banco de Dados Remoto (VPS)

Este guia explica como configurar o pipeline local para processar dados e salvá-los diretamente em um banco de dados PostgreSQL hospedado em uma VPS, sem precisar baixar os arquivos na VPS.

## Método Recomendado: Túnel SSH (Mais Seguro)

Esta é a maneira mais segura, pois não exige que você exponha a porta do banco de dados (5432) para a internet pública.

### 1. Criar o Túnel

Abra um terminal separado e execute o seguinte comando para redirecionar uma porta local (ex: `5433`) para a porta do Postgres na sua VPS (`5432`):

```bash
# Sintaxe: ssh -L <porta_local>:localhost:<porta_remota_db> <usuario>@<ip_vps>
ssh -L 5433:localhost:5432 usuario@ip-da-sua-vps
```

Mantenha esse terminal aberto enquanto estiver rodando o pipeline.

### 2. Configurar o `.env`

No seu arquivo `.env` local, aponte para a porta local do túnel (`5433`):

```bash
# Conecta na porta local 5433, que o SSH redireciona para a VPS
DATABASE_URL=postgres://usuario_db:senha_db@localhost:5433/nome_banco
```

### 3. Rodar o Pipeline

Agora o pipeline vai "pensar" que está conectando localmente, mas os dados estarão indo para a VPS.

```bash
just run
```

---

## Método Alternativo: Conexão Direta (Menos Seguro)

⚠️ **Atenção**: Este método exige expor o banco de dados para a internet, o que aumenta o risco de ataques. Use apenas se tiver firewalls (UFW/AWS Security Groups) restringindo o acesso apenas ao seu IP.

### 1. Configurar o PostgreSQL na VPS

Edite o arquivo `postgresql.conf` na VPS para aceitar conexões externas:

```conf
listen_addresses = '*'
```

Edite o arquivo `pg_hba.conf` para permitir seu IP:

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    all             all             seu.ip.de.casa/32       scram-sha-256
```

Reinicie o PostgreSQL.

### 2. Configurar o `.env`

Aponte diretamente para o IP público da VPS:

```bash
DATABASE_URL=postgres://usuario_db:senha_db@ip-da-sua-vps:5432/nome_banco
```
