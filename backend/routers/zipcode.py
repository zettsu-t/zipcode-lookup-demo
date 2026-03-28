import re
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import ken_all

router = APIRouter()


class ZipcodeResult(BaseModel):
    zipcode: str
    address: str


class ErrorDetail(BaseModel):
    detail: str


def normalize(code: str) -> str | None:
    """ハイフンあり・なし両方を受け付け、NNN-NNNN形式に正規化。不正ならNone。"""
    digits = code.replace("-", "")
    if not re.fullmatch(r"\d{7}", digits):
        return None
    return f"{digits[:3]}-{digits[3:]}"


@router.get(
    "/api/v1/zip",
    summary="郵便番号→住所の順引き",
    response_model=ZipcodeResult,
    responses={
        400: {"model": ErrorDetail, "description": "郵便番号のフォーマットが不正"},
        404: {"model": ErrorDetail, "description": "該当する郵便番号なし"},
    },
)
def get_zip(
    code: str = Query(
        ...,
        pattern=r"^[0-9]{7}$|^[0-9]{3}-[0-9]{4}$",
        description="郵便番号。ハイフンあり（NNN-NNNN）またはなし（NNNNNNN）",
        examples=["2310017", "231-0017"],
    ),
) -> ZipcodeResult:
    normalized = normalize(code)
    if normalized is None:
        return JSONResponse(status_code=400, content={"detail": "invalid zipcode format"})
    result = ken_all.lookup(normalized)
    if result is None:
        return JSONResponse(status_code=404, content={"detail": "zipcode not found"})
    return result
