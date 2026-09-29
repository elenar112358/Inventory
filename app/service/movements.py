from sqlalchemy.orm import Session

from app.schemas import MovementsPost, MovementsPostResponse, MovementsRequest, MovementsResponse, ProductsStock, \
    ProductSKUStock, ProductsForecastRequest, ProductsForecastResponse, AlertsResponse


def post_receipt(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    ...

def post_consume(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    ...

def post_writeoff(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    ...

def post_return(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    ...

def post_correction(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    ...

def get_movements(db: Session, query_params: MovementsRequest) -> MovementsResponse:
    ...

def get_stock(db: Session) -> ProductsStock:
    ...

def get_stock_by_sku(db: Session, sku: str) -> ProductSKUStock:
    ...

def get_forecast(db: Session, query_params: ProductsForecastRequest) -> ProductsForecastResponse:
    ...

def get_alerts(db: Session) -> AlertsResponse:
    ...


