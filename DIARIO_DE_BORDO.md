# 🏁 Diário de Bordo do Projeto Kart Amateur Championship

Este log registra as decisões estratégicas, ajustes de UX e marcos de infraestrutura tomados durante o desenvolvimento do MVP (Produto Mínimo Viável).

## Status Atual
* **Fase:** Lançado em Produção (pisafundo.site)
* **Infraestrutura:** Docker + EasyPanel (VPS) + PostgreSQL
* **Código:** GitHub (jailsonmendesjr/kart-championship)

## Log de Desenvolvimento (13/12/2025)

| Seção | Título do Marco/Ajuste | Detalhes e Justificativa |
| :--- | :--- | :--- |
| **Frontend/UX** | **Tabelas Responsivas (Stacked)** | Implementado o design "Empilhado" (Stacked) para as tabelas de Ranking e Resultados. No mobile, a coluna "Equipe" some, e o nome da equipe aparece com a cor primária logo abaixo do nome do piloto. **Motivo:** Evitar o scroll horizontal e melhorar a usabilidade em telas pequenas. |
| **Frontend/UX** | **Carrossel de Etapas** | O Calendário de Etapas na página da temporada foi transformado de uma lista vertical em um **Carrossel Horizontal** (Scroll Snap). **Motivo:** Evitar que a lista longa empurrasse o Ranking para fora da tela no mobile, otimizando o acesso à informação principal. |
| **Backend/Lógica** | **Indicadores de Evolução (Setinhas)** | Implementada a lógica de comparação de rankings na `views.py`. O sistema calcula o ranking atual vs. o ranking até a penúltima etapa e exibe as setas ▲ (subiu) ou ▼ (caiu). **Motivo:** Trazer o aspecto de competição viva para a classificação geral. |
| **Backend/Dados** | **Importação em Massa** | **Decisão:** Abortada a implementação de upload de CSV/Excel. **Motivo:** Manter a simplicidade e a segurança do MVP, utilizando o Django Admin para cadastro inicial. |
| **Infraestrutura** | **Containerização e Deploy** | Criação do `Dockerfile`, ajuste do `settings.py` para usar variáveis de ambiente (`SECRET_KEY`, `DATABASE_URL`, `HOST`) e deploy bem-sucedido no **EasyPanel**. |
| **Segurança** | **Configuração CSRF/Host** | Resolvido o erro 403 (CSRF) no deploy de produção através da variável `HOST` no EasyPanel, configurada com os domínios `pisafundo.site,www.pisafundo.site`. **Motivo:** Garantir que o Django confie no domínio final, permitindo logins e requisições seguras. |
| **Infraestrutura** | **Domínio Personalizado** | Configuração final do DNS na Hostinger (substituição do Registro A pelo IP da VPS) e no EasyPanel. **Resultado:** O site está acessível via `https://pisafundo.site`. |

