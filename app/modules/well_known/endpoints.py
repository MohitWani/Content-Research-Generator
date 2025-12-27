"""Well-known endpoints for JWKS and other discovery endpoints."""

from fastapi import APIRouter

from app.core.auth.jwks_service import jwks_service

well_known_router = APIRouter(tags=['Well-Known'])


@well_known_router.get('/jwks.json')
async def get_jwks():
    """Get JSON Web Key Set (JWKS) for JWT verification."""
    return jwks_service.getJWKS()
