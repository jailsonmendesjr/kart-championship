# Kart Amateur Championship – Status do Projeto (MVP)

> **Data de Atualização:** 13/12/2025
> **Fase Atual:** MVP (Funcional em Localhost) - Pronto para Containerização (Docker)
> **Stack:** Django (Monolito) + Tailwind CSS (CDN) + SQLite (Dev)

## 1. Visão Geral
Sistema de gerenciamento de campeonatos de kart amador. O foco é eliminar planilhas, garantindo integridade de dados e oferecendo uma visualização pública (Mobile First) dos rankings e resultados.

## 2. Estrutura Técnica e Decisões
Optou-se pela abordagem **Monolito (Django + Templates)** para agilidade de desenvolvimento e facilidade de manutenção pelo perfil Designer/PM.

* **Backend:** Python 3.11+ / Django 4.x
* **Frontend:** Django Templates (HTML) + Tailwind CSS (via CDN Script).
* **Interatividade:** JavaScript Vanilla (para abas e menus) + Alpine.js (opcional, mas JS puro foi usado na maior parte).
* **Banco de Dados:** SQLite (Desenvolvimento), PostgreSQL (Produção - VPS).

## 3. Banco de Dados e Modelos (`models.py`)

### Principais Entidades:
1.  **Season (Temporada):** Ano e Nome (ex: 2025). Pode estar ativa ou não.
2.  **Team (Equipe):** Nome, Slug, **Cor Primária** (Hex), Cor Secundária.
3.  **Driver (Piloto):** Nome, Apelido, Número, Slug.
4.  **DriverTeamSeason (Inscrição):** Tabela pivô que vincula Piloto + Equipe + Temporada.
    * *Regra de Negócio:* Máximo de 2 pilotos por equipe na mesma temporada (Validado no `clean()`).
    * *Regra de Negócio:* Um piloto só pode estar em 1 equipe por temporada.
5.  **Round (Etapa):** Nome, Data, Local, Ordem.
6.  **RoundResult (Resultado):** Vincula Etapa + Inscrição.
    * *Campos:* Posição (1-20+), Volta Mais Rápida (Boolean), Pontos (Calculado).
    * *Regra de Negócio:* Pontuação baseada na F1 (25, 18, 15...).
    * *Regra de Negócio:* Volta Mais Rápida soma +1 ponto.
    * *Validação:* Não permite dois pilotos na mesma Posição na mesma etapa.
    * *Validação:* Não permite dois pilotos com Volta Mais Rápida na mesma etapa.

## 4. Funcionalidades de Frontend e UX

### Visualização de Temporada (`season_detail.html`)
* **Calendário de Etapas:** Implementado como **Carrossel Horizontal** (Scroll Snap).
    * *Motivo:* Economizar espaço vertical no mobile e evitar scroll infinito antes do ranking.
* **Ranking (Tabs):** Sistema de abas alternando entre "Ranking de Pilotos" e "Ranking de Equipes".
* **Indicadores de Evolução:** Setas (▲/▼) indicando se o piloto subiu ou desceu posições em relação ao acumulado até a etapa anterior.
    * *Lógica:* Comparação dinâmica feita na View (`views.py`). Se for a 1ª etapa, mostra "-".

### Visualização de Etapa (`round_detail.html`)
* **Tabelas Empilhadas (Stacked):**
    * *Desktop:* Colunas: Pos | Piloto | Equipe | V. Rápida | Pontos.
    * *Mobile:* Colunas: Pos | Piloto (Nome da Equipe aparece abaixo do nome do piloto) | Pts.
* **Identidade Visual:** Uso da `primary_color` da equipe como uma "bolinha" ao lado do nome (Mobile) ou borda colorida (Desktop).
* **Destaques:** Emojis de troféus (🏆, 🥈, 🥉) para o Top 3. Emoji de cronômetro (⏱️) para volta rápida.

## 5. Lógica de Backend Crítica (`views.py`)

* **Cálculo de Pontos:** Feito via `annotate` e `Sum` do Django ORM.
* **Função `calculate_standings`:**
    * Calcula o ranking somando todos os pontos.
    * Possui flag `exclude_last_round=True` para permitir calcular o ranking "passado" e gerar as setinhas de evolução.
* **Importação de Dados:**
    * *Decisão:* Abortada a implementação de upload de CSV/Excel neste momento para manter o MVP simples e seguro.
    * *Fluxo:* Cadastro feito manualmente via Django Admin (que é otimizado com `Inlines`).

## 6. Próximos Passos (Roadmap)

1.  **Containerização:** Criar `Dockerfile` e `docker-compose.yml`.
2.  **Deploy:** Configurar repositório GitHub e conectar ao **EasyPanel** na VPS.
3.  **Configuração Prod:** Ajustar `settings.py` para ler variáveis de ambiente (`.env`) e servir arquivos estáticos via WhiteNoise ou Nginx.
4.  **Domain/SSL:** Configurar domínio final e HTTPS.

---
