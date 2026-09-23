from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from typing import Literal
import member_accounts as accounts
import referrals

router = APIRouter(prefix='/v1/referral', tags=['referral'])


class Claim(BaseModel):
    code: str = Field(min_length=20, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    relation: Literal['lover','family','relative','friend','coworker','other'] = 'other'


@router.post('/invite')
def invite(authorization: str | None = Header(default=None)):
    account = accounts.authenticate(authorization)
    return {'code':referrals.invite(account), 'credit':referrals.status(account),
            'comparisons':referrals.comparisons(account)}


@router.post('/claim')
def claim(req: Claim, authorization: str | None = Header(default=None)):
    account = accounts.authenticate(authorization)
    return {'credit':referrals.claim(account, req.code, req.relation),
            'comparisons':referrals.comparisons(account)}


@router.post('/comparisons')
def comparisons(authorization: str | None = Header(default=None)):
    return {'comparisons':referrals.comparisons(accounts.authenticate(authorization))}
