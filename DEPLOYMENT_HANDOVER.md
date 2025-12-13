# 📦 Deployment Handover (Entrega de Implantação)

Este documento lista as configurações críticas e operacionais do sistema Kart Amateur Championship, destinadas à manutenção e reimplementação.

## Informações do Projeto

| Item | Detalhes da Configuração |
| :--- | :--- |
| **Projeto/App Name** | Kart Championship Backend |
| **Domínio Ativo** | `https://pisafundo.site` |
| **Repositório Git** | `https://github.com/jailsonmendesjr/kart-championship.git` (Branch: `main`) |
| **Ambiente de Hosting** | EasyPanel (VPS) |
| **Banco de Dados** | PostgreSQL (EasyPanel Service: `db`) |

## Variáveis de Ambiente e Segurança (EasyPanel)

As variáveis abaixo são injetadas no container do serviço `backend`. **Os valores reais são armazenados APENAS no painel do EasyPanel.**

| Variável | Função | Valor no EasyPanel |
| :--- | :--- | :--- |
| **`SECRET_KEY`** | Chave Secreta do Django (Segurança Crítica) | *(Valor armazenado no EasyPanel)* |
| **`DATABASE_URL`** | String de Conexão com o PostgreSQL | *(Valor armazenado no EasyPanel)* |
| **`HOST`** | Domínios confiáveis (`ALLOWED_HOSTS`) | `pisafundo.site,www.pisafundo.site` |
| **`DEBUG`** | Modo de Operação | `False` (Produção) |

## Comandos Operacionais (Console EasyPanel)

Para manutenção (após cada deploy ou em caso de erro no banco de dados):

| Ação | Comando a ser executado |
| :--- | :--- |
| **Aplicar Migrações** (Criar/atualizar tabelas) | `python manage.py migrate` |
| **Criar/Resetar Admin** (Superuser) | `python manage.py createsuperuser` |
| **Coletar Estáticos** (Gerar CSS/JS) | `python manage.py collectstatic --noinput` |

## Outras Notas de Operação

* **Acesso Admin:** Disponível em `https://pisafundo.site/admin/`
* **Serviço:** O servidor web é o **Gunicorn**, iniciado pelo `Dockerfile`.
* **Arquivos Estáticos:** Servidos pelo **WhiteNoise** (integrado ao Django).