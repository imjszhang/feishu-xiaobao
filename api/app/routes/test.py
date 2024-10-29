import os
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..dependencies import verify_api_key
from ..dependencies import verify_local_request

router = APIRouter()


# 创建一个根路由
@router.get("/", dependencies=[Depends(verify_api_key)])
def read_root():  
    return {"message": "Hello World"}