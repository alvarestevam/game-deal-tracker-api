# GameDeal Tracker API 🎮💰

O **GameDeal Tracker** é uma API robusta desenvolvida com **FastAPI** para o monitoramento centralizado de ofertas, promoções e jogos gratuitos (giveaways) para PC. O sistema agrega dados de múltiplas fontes, realiza auditoria de preços comparando com históricos reais e converte automaticamente valores de USD para BRL.

## 🚀 Arquitetura e Tecnologias

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Banco de Dados:** [PostgreSQL](https://www.postgresql.org/) (com SQLAlchemy e AsyncPG para operações assíncronas)
- **Containerização:** [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)
- **Proxy Reverso:** [Caddy](https://caddyserver.com/) (com suporte nativo a HTTPS)
- **Sincronização:** Rotinas automáticas via `APScheduler` integradas ao ciclo de vida da aplicação.

## 📊 Fontes de Dados

A API consome dados em tempo real das seguintes plataformas:

1.  **IsThereAnyDeal (ITAD):** Principal fonte para ofertas detalhadas e histórico de preços (Historical Low).
2.  **CheapShark:** Monitoramento de descontos em diversas lojas digitais (Steam, GOG, Humble Store, etc.).
3.  **GamerPower:** Rastreamento especializado em Giveaways (jogos 100% gratuitos).
4.  **AwesomeAPI:** Cotação atualizada do USD para BRL para conversão precisa de preços.

## 📂 Estrutura do Banco de Dados

O modelo principal `Game` armazena as seguintes informações:

- `id`: Identificador único (UUID).
- `title`: Título do jogo (Chave de busca e unicidade).
- `current_price`: Preço atual da oferta (em BRL).
- `historical_low`: Menor preço já registrado no sistema (em BRL).
- `is_free`: Booleano indicando se o jogo está gratuito.
- `store_name`: Nome da loja que oferece o desconto.
- `deal_url`: Link direto para a oferta.
- `image_url`: URL da imagem/banner em alta resolução.
- `promo_start_date` / `promo_end_date`: Datas de validade da promoção.
- `is_active`: Status da oferta (Sincronização reativa).

## 🛠️ Setup e Execução

### Pré-requisitos
- Docker e Docker Compose instalados.
- Chave de API do IsThereAnyDeal ([Solicite aqui](https://isthereanydeal.com/apps/my/)).

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <repository-url>
    cd gamedeal-tracker
    ```

2.  **Configure as variáveis de ambiente:**
    Copie o arquivo de exemplo e preencha com suas credenciais:
    ```bash
    cp .env.example .env
    ```

3.  **Inicie os containers:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Acesse a documentação interativa:**
    Acesse `http://localhost:8000/docs` (ou via Caddy no domínio configurado) para visualizar todos os endpoints disponíveis.

## 🔐 Segurança e Rate Limiting

- **API Key:** Endpoints protegidos exigem o header `X-API-Key`.
- **Sync Key:** O endpoint de sincronização manual exige `X-Sync-API-Key`.
- **Limiter:** Implementado rate limit por IP para garantir a estabilidade do serviço.

## 🧪 Testes

Para executar a suite de testes unitários:
```bash
pip install -r requirements.txt
export PYTHONPATH=.
pytest
```

---
*Desenvolvido para entusiastas de jogos que buscam economia e eficiência.*
