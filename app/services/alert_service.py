from app.models.game import Game, GameOffer

def _calculate_deal_score(game: Game, offer: GameOffer) -> float:
    """
    Calcula uma nota de oportunidade de 0 a 10 baseada na agressividade do desconto
    e se bateu o preço histórico.
    """
    score = 0.0

    # 1. Baseado no desconto (até 7 pontos)
    if offer.original_price and offer.original_price > 0:
        discount_percent = (1 - (offer.current_price / offer.original_price)) * 100
        # Ex: 50% de desconto = 3.5 pontos, 90% = 6.3 pontos, 100% = 7 pontos
        score += (discount_percent / 100) * 7
    elif offer.current_price == 0:
        # Giveaways ganham pontuação máxima de desconto
        score += 7.0

    # 2. Baseado no preço histórico (3 pontos extras)
    if offer.current_price <= offer.historical_low:
        score += 3.0

    return round(min(score, 10.0), 1)

def should_send_alert(game: Game, offer: GameOffer) -> bool:
    """
    Filtra os jogos da sincronização com base em qualidade/desconto.
    Regra:
    - Se tiver nota no Metacritic, deve ser >= 75.
    - O desconto deve ser > 50% OU atingiu o menor preço histórico.
    """
    # Filtro Metacritic
    if game.metacritic_score is not None and game.metacritic_score < 75:
        return False

    # Filtro de preço/desconto
    is_historical_low = offer.current_price <= offer.historical_low

    has_good_discount = False
    if offer.original_price and offer.original_price > 0:
        discount_percent = (1 - (offer.current_price / offer.original_price)) * 100
        if discount_percent > 50:
            has_good_discount = True
    elif offer.current_price == 0:
        has_good_discount = True # Grátis é sempre bom desconto

    return has_good_discount or is_historical_low

def format_alert_message(game: Game, offer: GameOffer) -> str:
    """
    Gera uma string formatada em Markdown pronta para redes sociais.
    """
    deal_score = _calculate_deal_score(game, offer)
    is_historical_low = offer.current_price <= offer.historical_low

    # Marcadores visuais
    historical_low_badge = "🚨 **MENOR PREÇO HISTÓRICO!** 🚨\n" if is_historical_low else ""
    metacritic_badge = f"⭐ Metacritic: {game.metacritic_score}\n" if game.metacritic_score else ""

    original_price_str = f"R$ {offer.original_price:,.2f}" if offer.original_price else "N/A"
    current_price_str = "GRÁTIS" if offer.current_price == 0 else f"R$ {offer.current_price:,.2f}"

    message = (
        f"🎮 **{game.title}**\n\n"
        f"{historical_low_badge}"
        f"{metacritic_badge}"
        f"💎 Deal Score: {deal_score}/10\n\n"
        f"💰 Preço Original: ~~{original_price_str}~~\n"
        f"🔥 **Preço Atual: {current_price_str}**\n"
        f"💳 **Fatura Estimada (c/ IOF): R$ {offer.estimated_final_price:,.2f}**\n\n"
        f"🔗 Link da Oferta: {offer.deal_url}\n"
    )

    return message
