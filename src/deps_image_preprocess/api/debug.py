from fastapi import APIRouter, status
from fastapi.responses import Response

router = APIRouter(tags=["Debug"])


@router.get("/debug/500", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
def raise_internal_server_error():
    raise ValueError()


@router.get("/healthcheck")
def service_healthcheck():
    return Response(status_code=status.HTTP_200_OK)
