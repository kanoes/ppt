"""Authentication helpers shared across HTML and PPT endpoints."""

import os
import traceback
from base64 import b64encode
from typing import Optional

from aiohttp import ClientSession
from dotenv import load_dotenv
from fastapi import Cookie, HTTPException, Request

from shared.logging import get_logger

load_dotenv()

logger = get_logger("auth")


async def verify_session_token(
    session_token: str | None, required_service: str = "ppt"
) -> tuple[bool, str, dict | None, str]:
    core_auth_root_url = os.environ.get("COREAUTH_ROOT_URL")
    core_auth_app_id = os.environ.get("COREAUTH_APP_ID")
    core_auth_app_secret = os.environ.get("COREAUTH_APP_SECRET")

    if not all([session_token, core_auth_root_url, core_auth_app_id, core_auth_app_secret]):
        logger.warning({
            "auth": {
                "status": "Configuration Missing",
                "message": "Core-Auth configuration not complete"
            }
        })
        return False, "configurationError", None, ""

    try:
        credentials = f"{core_auth_app_id}:{core_auth_app_secret}"
        headers = {
            "Authorization": f"Basic {b64encode(credentials.encode('utf-8')).decode('utf-8')}",
            "Content-Type": "application/json"
        }
        payload = {"sessionToken": session_token}

        async with ClientSession(core_auth_root_url) as session:
            async with session.post(
                "/auth-bot/verify-session", json=payload, headers=headers
            ) as auth_response:
                auth_response.raise_for_status()
                auth_data = await auth_response.json()
                
                auth_status = auth_data.get("status", "failed")
                user_properties = auth_data.get("properties", None)
                valid_for = auth_data.get("validFor", "")

                if auth_status != "active":
                    logger.warning({
                        "auth": {
                            "status": "Token Inactive",
                            "authStatus": auth_status
                        }
                    })
                    return False, auth_status, None, ""

                valid_for_list = [s.strip() for s in valid_for.split(",") if s.strip()]
                
                if required_service and required_service not in valid_for_list:
                    logger.warning({
                        "auth": {
                            "status": "Service Not Authorized",
                            "requiredService": required_service,
                            "validFor": valid_for,
                            "displayName": auth_data.get("displayName", "Unknown")
                        }
                    })
                    return False, "serviceNotAuthorized", None, valid_for

                logger.info({
                    "auth": {
                        "status": "Session Verified",
                        "displayName": auth_data.get("displayName", "Unknown"),
                        "validFor": valid_for,
                        "service": required_service
                    }
                })
                
                return True, auth_status, user_properties, valid_for

    except Exception as e:
        logger.error({
            "auth": {
                "status": "Verification Failed",
                "error": str(e),
                "trace": traceback.format_exc()
            }
        })
        return False, "tokenValidationFailed", None, ""


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

    is_valid, status, user_properties, valid_for = await verify_session_token(
        market_session_token, required_service="ppt"
    )

    if not is_valid:
        if status == "serviceNotAuthorized":
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

