"""
Supabase JWT Authentication Helper

This module provides JWT verification for Supabase tokens.
Currently not enforced on any endpoints - for future use.
"""
from typing import Optional
from fastapi import Header, HTTPException, status
import jwt
from jwt import PyJWTError

from .config import SUPABASE_JWT_SECRET, SUPABASE_URL


def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Optional JWT token verification. Returns user data if valid token provided,
    None if no token or invalid token.

    This is NOT enforced - endpoints will work with or without authentication.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        dict: User data from JWT payload if valid, None otherwise
    """
    if not authorization:
        return None

    if not SUPABASE_JWT_SECRET:
        # Supabase not configured, skip verification
        return None

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            return None

        # Verify and decode JWT
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role'),
        }
    except (PyJWTError, ValueError, AttributeError):
        # Invalid token, but we don't enforce auth, so return None
        return None


async def verify_supabase_token(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    STRICT JWT token verification (for future protected endpoints).
    Raises HTTPException if token is missing or invalid.

    NOT CURRENTLY USED - All endpoints remain public.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        dict: User data from JWT payload

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role'),
        }
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id_from_token(authorization: Optional[str] = None) -> Optional[str]:
    """
    Helper to extract user_id from JWT token without raising exceptions.

    Args:
        authorization: Bearer token string

    Returns:
        str: User ID if token is valid, None otherwise
    """
    user_data = get_current_user_optional(authorization)
    return user_data.get('user_id') if user_data else None