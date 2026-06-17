from app.models.game import Game, GameOffer

def format_alert_message(game: Game, offer: GameOffer) -> str:
    """
    Gera uma string formatada em Markdown pronta para redes sociais.
    """
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
        f"💰 Preço Original: ~~{original_price_str}~~\n"
        f"🔥 **Preço Atual: {current_price_str}**\n"
        f"💳 **Fatura Estimada (c/ IOF): R$ {offer.estimated_final_price:,.2f}**\n\n"
        f"🔗 Link da Oferta: {offer.deal_url}\n"
    )

    return message
