from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import jigyosyo, ken_all

router = APIRouter()

_LIMIT = 100


class AddressResult(BaseModel):
    zipcode: str
    address: str
    type: str


class ErrorDetail(BaseModel):
    detail: str


@router.get(
    "/api/v2/address",
    summary="住所→郵便番号の逆引き",
    response_model=list[AddressResult],
    responses={400: {"model": ErrorDetail, "description": "クエリが短すぎる"}},
)
def get_address(
    q: str = Query(..., description="検索クエリ。2文字以上。ワイルドカード * 使用可"),
):
    if len(q) <= 1:
        return JSONResponse(status_code=400, content={"detail": "query too short"})

    fetch = _LIMIT + 1

    jg = jigyosyo.search(q, limit=fetch)
    if len(jg) >= fetch:
        return []

    ge = ken_all.search(q, limit=fetch - len(jg))
    if len(jg) + len(ge) > _LIMIT:
        return []

    return jg + ge
