from app.services.market_data_service import MarketDataService


class DatasetService:
    @staticmethod
    def import_dataset(payload: dict) -> dict:
        return MarketDataService.import_dataset(payload)

    @staticmethod
    def list_datasets() -> list[dict]:
        return MarketDataService.list_datasets()
