"""Authentication helpers shared across HTML and PPT endpoints."""

import traceback
from base64 import b64encode
from typing import Optional

from aiohttp import ClientSession
from fastapi import Cookie, HTTPException, Request

from shared.config import settings
from shared.logging import get_logger

logger = get_logger("auth")


async def verify_session_token(
    session_token: str | None, required_service: str = "ppt"
) -> tuple[bool, str, dict | None, list[str]]:
    core_auth_root_url = settings.coreauth_root_url
    core_auth_app_id = settings.coreauth_app_id
    core_auth_app_secret = settings.coreauth_app_secret

    if not all([session_token, core_auth_root_url, core_auth_app_id, core_auth_app_secret]):
        logger.warning({
            "auth": {
                "status": "Configuration Missing",
                "message": "Core-Auth configuration not complete"
            }
        })
        return False, "configurationError", None, []

    try:
        credentials = f"{core_auth_app_id}:{core_auth_app_secret}"
        headers = {
            "Authorization": f"Basic {b64encode(credentials.encode('utf-8')).decode('utf-8')}",
            "Content-Type": "application/json"
        }
        payload = {
            "sessionToken": session_token,
            "requiredSubApp": required_service
        }

        async with ClientSession(core_auth_root_url) as session:
            async with session.post(
                "/auth-bot/verify-sub-session", json=payload, headers=headers
            ) as auth_response:
                auth_response.raise_for_status()
                auth_data = await auth_response.json()
                
                auth_status = auth_data.get("status", "failed")
                user_properties = auth_data.get("properties", None)

                if auth_status != "active":
                    logger.warning({
                        "auth": {
                            "status": "Token Inactive",
                            "authStatus": auth_status
                        }
                    })
                    return False, auth_status, None, []

                logger.info({
                    "auth": {
                        "status": "Session Verified",
                        "displayName": auth_data.get("displayName", "Unknown"),
                        "service": required_service
                    }
                })
                
                return True, auth_status, user_properties

    except Exception as e:
        logger.error({
            "auth": {
                "status": "Verification Failed",
                "error": str(e),
                "trace": traceback.format_exc()
            }
        })
        return False, "tokenValidationFailed", None, []


async def get_current_user(
    request: Request,
    market_session_token: Optional[str] = Cookie(None, alias="MarketSessionToken")
):
    if not market_session_token:
        logger.warning({
            "auth": {
                "status": "No Token Provided",
                "path": request.url.path
            }
        })
        raise HTTPException(
            status_code=401,
            detail="Authentication required: No session token provided"
        )

    is_valid, status, user_properties = await verify_session_token(
        market_session_token, required_service="ppt"
    )

    if not is_valid:
        if status == "subAppNotAuthorized":
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token not valid for PPT service"
            )
        elif status == "tokenExpired":
            raise HTTPException(
                status_code=401,
                detail="Authentication expired: Please login again"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: {status}"
            )

    return user_properties

