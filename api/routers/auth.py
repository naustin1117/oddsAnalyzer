"""
Authentication endpoints (for testing/debugging)
"""
from fastapi import APIRouter, Depends, Header
from typing import Optional

from ..supabase_auth import get_current_user_optional, verify_supabase_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
async def get_current_user(
    authorization: Optional[str] = Header(None)
):
    """
    Get current authenticated user info (if logged in).
    Returns null if not authenticated.

    This endpoint does NOT require authentication - it simply returns
    user info if a valid token is provided.
    """
    user = get_current_user_optional(authorization)

    if user:
        return {
            "authenticated": True,
            "user": user
        }
    else:
        return {
            "authenticated": False,
            "user": None
        }


@router.get("/test-protected")
async def test_protected_endpoint(
    user: dict = Depends(verify_supabase_token)
):
    """
    Example of a PROTECTED endpoint (for future reference).

    This endpoint REQUIRES authentication and will return 401 if not logged in.
    This is NOT used anywhere in the app yet - just an example.
    """
    return {
        "message": "You are authenticated!",
        "user": user
    }