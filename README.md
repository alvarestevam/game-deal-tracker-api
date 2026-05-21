Documento de Escopo de Projeto: GameDeal Tracker
1. Visão Geral do Projeto

Desenvolvimento de um aplicativo móvel (cliente) e uma API proprietária (servidor) destinados ao monitoramento unificado de promoções de jogos de PC e resgate de títulos gratuitos. O sistema atuará como um agregador e auditor de preços, garantindo que descontos sejam validados contra dados históricos reais antes de notificar o usuário. Todo o processamento de backend, rotinas de busca e banco de dados estarão centralizados em uma infraestrutura própria hospedada em uma máquina virtual (Oracle VM).
2. Objetivos

    Centralização: Unificar as informações de mais de 20 lojas de distribuição digital (Steam, Epic, GOG, etc.) em uma única interface nativa.

    Auditoria de Valores: Cruzar preços atuais com o menor preço histórico (historical low) para validar a veracidade das promoções.

    Notificações Pró-ativas: Eliminar a necessidade de verificação manual por meio de alertas automatizados baseados em regras de preços-alvo definidos na Watchlist.

    Otimização de Hardware e Aquisições: Direcionar o foco das ofertas primariamente para plataformas de PC, maximizando a biblioteca de jogos sem gastos desnecessários.

3. Arquitetura e Stack Tecnológico

A infraestrutura seguirá o modelo cliente-servidor, separando claramente a camada de apresentação da camada de ingestão de dados.

    Infraestrutura Cloud: Oracle VM (Hospedagem do servidor web, banco de dados e rotinas de ingestão).

    Backend (API): Python utilizando o framework FastAPI para alta performance e criação de endpoints RESTful rápidos.

    Processamento Assíncrono: Celery (ou APScheduler) para executar rotinas agendadas (cron jobs) de consulta às APIs externas sem bloquear o servidor principal.

    Banco de Dados: PostgreSQL para armazenamento relacional seguro do histórico de preços em cache e dados da Watchlist.

    Frontend (App Mobile): Flutter (Dart) para compilação multiplataforma, focado em performance de renderização de listas e gráficos.

    APIs Externas Consumidas:

        CheapShark API: Dados de descontos atuais e Deal Rating.

        IsThereAnyDeal (ITAD) API: Gráficos de flutuação e menor preço histórico.

        GamerPower API: Rastreamento de jogos 100% gratuitos (giveaways).

4. Escopo Funcional (Funcionalidades do Aplicativo)
4.1. Radar de Gratuidade (Aba Giveaways)

    Listagem em tempo real de jogos base, expansões ou DLCs que estejam com 100% de desconto em lojas cadastradas.

    Botões de redirecionamento direto para a página de resgate nas lojas oficiais.

4.2. Auditoria e Busca de Jogos

    Barra de pesquisa para consulta de títulos específicos.

    Tela de detalhes do jogo contendo:

        Preço original vs. Preço atual.

        Gráfico simples exibindo a curva do histórico de preço.

        Indicador visual (Selo) sinalizando se é o melhor momento de compra ("Historical Low Atingido" ou "Aguarde melhor oferta").

4.3. Watchlist Inteligente e Alertas

    Capacidade de adicionar jogos à lista de desejos.

    Definição de parâmetros de alerta: notificar apenas se o jogo ficar abaixo de X reais ou se o desconto ultrapassar Y%.

    Integração com serviço de Push Notifications (via Firebase Cloud Messaging) para envio de alertas ao dispositivo móvel.

5. Fases de Desenvolvimento e Entregáveis

    Fase 1: Configuração da Infraestrutura (Servidor e Banco de Dados)

        Configuração da Oracle VM, regras de firewall e deploy do banco de dados PostgreSQL.

        Estruturação do projeto FastAPI e criação das rotas e modelos de dados (pode ser delegado ao Jules).

    Fase 2: Motor de Ingestão e Integração de APIs

        Criação dos scripts Python responsáveis por fazer o fetch (busca) no CheapShark, ITAD e GamerPower.

        Implementação de um sistema de conversão de moedas (USD para BRL) em tempo real ou via cache diário.

    Fase 3: Desenvolvimento Frontend (Interface Mobile)

        Desenho e estruturação das telas no Flutter.

        Implementação das chamadas HTTP no aplicativo para consumir a API criada na Fase 1.

    Fase 4: Notificações e Polimento

        Integração do sistema de Push Notifications.

        Testes de estresse na API e refinamento do design do aplicativo.

6. Fora do Escopo (Não será desenvolvido nesta versão)

    Sistema de Compras In-App: O aplicativo não processará pagamentos; ele apenas redirecionará o usuário, via link, para a loja oficial (Steam, Epic, etc.).

    Rede Social: Recursos de amizade, fóruns ou chat integrados não farão parte deste produto.

    Múltiplos Perfis de Usuário complexos: Inicialmente focado no uso pessoal ou instâncias isoladas, sem necessidade imediata de um sistema de login com permissões complexas de controle de acesso (RBAC).
