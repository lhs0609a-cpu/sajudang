from typing import Literal
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
import activity
import store

router = APIRouter(prefix='/v1/activity', tags=['activity'])


@router.get('/promotion')
def promotion(response: Response):
    import promotions
    response.headers['Cache-Control'] = 'no-store'
    return {'promotion': promotions.current()}


class Presence(BaseModel):
    visitor: str = Field(min_length=16, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    screen: Literal['entry', 'seats', 'reading']


@router.post('')
def heartbeat(req: Presence, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    try:
        return activity.snapshot(req.visitor, req.screen)
    except store.LeaseBusy:
        raise HTTPException(503, '잠시 후 다시 확인해 주세요.')
