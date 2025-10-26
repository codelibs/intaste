# Copyright (c) 2025 CodeLibs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
API authentication using X-Intaste-Token header.
"""

from fastapi import Header, HTTPException, status

from ...i18n import _
from ..config import settings


async def verify_api_token(
    x_intaste_token: str | None = Header(None, alias="X-Intaste-Token")
) -> str:
    """
    Verify the API token from X-Intaste-Token header.

    Args:
        x_intaste_token: Token from header

    Returns:
        The validated token

    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    if not x_intaste_token or x_intaste_token != settings.intaste_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": _("Invalid or missing API token", language="en"),
            },
        )
    return x_intaste_token
