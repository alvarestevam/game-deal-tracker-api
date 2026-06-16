import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.sync_service import sync_games, BLACK_LIST_KEYWORDS
from app.models.game import Game, GameOffer

@pytest.mark.asyncio
async def test_blacklist_filtering():
    # Mocking environment variables required for settings validation
    with patch.dict("os.environ", {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "testdb",
        "POSTGRES_PORT": "5432",
        "API_KEY": "test",
        "SYNC_API_KEY": "test"
    }):
        # Setup mocks
        with patch("app.services.sync_service.GamerPowerClient") as MockGP, \
             patch("app.services.sync_service.CheapSharkClient") as MockCS, \
             patch("app.services.sync_service.ITADClient") as MockITAD, \
             patch("app.services.sync_service.AsyncSessionLocal") as MockSessionLocal, \
             patch("app.services.sync_service.get_usd_brl_rate", return_value=5.0), \
             patch("app.services.sync_service.calculate_deal_score", return_value=10.0), \
             patch("app.services.sync_service.send_telegram_alert", new_callable=AsyncMock) as mock_send:

            # Mock clients to return empty lists to skip sync part
            MockGP.return_value.get_pc_giveaways = AsyncMock(return_value=[])
            MockCS.return_value.get_deals = AsyncMock(return_value=[])
            MockITAD.return_value.get_deals = AsyncMock(return_value=[])

            # Mock session
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            MockSessionLocal.return_value = mock_session

            # Mock pending offers
            game_dlc = Game(title="The Witcher 3: Wild Hunt - Expansion Pass", slug="the-witcher-3-expansion-pass")
            offer_dlc = GameOffer(game=game_dlc, is_active=True, notified_telegram=False, current_price=0.0, store_name="Steam", historical_low=0.0, deal_url="http://test.com/dlc")

            game_legit = Game(title="Cyberpunk 2077", slug="cyberpunk-2077")
            offer_legit = GameOffer(game=game_legit, is_active=True, notified_telegram=False, current_price=0.0, store_name="Steam", historical_low=0.0, deal_url="http://test.com/game")

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [offer_dlc, offer_legit]
            mock_session.execute.return_value = mock_result

            # Run sync_games
            await sync_games()

            # Assertions
            # Both should be marked as notified (DLC because it was skipped, legit because it was sent)
            assert offer_dlc.notified_telegram is True
            assert offer_legit.notified_telegram is True

            # Verify send_telegram_alert was NOT called for DLC but WAS called for legit game
            # mock_send should have been called exactly once for "Cyberpunk 2077"
            assert mock_send.call_count == 1
            args, kwargs = mock_send.call_args
            assert kwargs['game_title'] == "Cyberpunk 2077"

@pytest.mark.asyncio
async def test_blacklist_all_keywords():
    from app.services.sync_service import BLACK_LIST_KEYWORDS

    with patch.dict("os.environ", {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "testdb",
        "POSTGRES_PORT": "5432",
        "API_KEY": "test",
        "SYNC_API_KEY": "test"
    }):
        for keyword in BLACK_LIST_KEYWORDS:
            with patch("app.services.sync_service.GamerPowerClient") as MockGP, \
                 patch("app.services.sync_service.CheapSharkClient") as MockCS, \
                 patch("app.services.sync_service.ITADClient") as MockITAD, \
                 patch("app.services.sync_service.AsyncSessionLocal") as MockSessionLocal, \
                 patch("app.services.sync_service.get_usd_brl_rate", return_value=5.0), \
                 patch("app.services.sync_service.send_telegram_alert", new_callable=AsyncMock) as mock_send:

                MockGP.return_value.get_pc_giveaways = AsyncMock(return_value=[])
                MockCS.return_value.get_deals = AsyncMock(return_value=[])
                MockITAD.return_value.get_deals = AsyncMock(return_value=[])

                mock_session = AsyncMock()
                mock_session.__aenter__.return_value = mock_session
                MockSessionLocal.return_value = mock_session

                title = f"Some Game {keyword.upper()}"
                game = Game(title=title, slug="some-game")
                offer = GameOffer(game=game, is_active=True, notified_telegram=False, current_price=0.0)

                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [offer]
                mock_session.execute.return_value = mock_result

                await sync_games()

                assert offer.notified_telegram is True
                mock_send.assert_not_called()
