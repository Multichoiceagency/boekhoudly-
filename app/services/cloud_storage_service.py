"""
Cloud Storage Integration Service
Supports Google Drive, Dropbox, and OneDrive for document import/export.
"""
import httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode
from app.config import get_settings

settings = get_settings()


class GoogleDriveService:
    """Google Drive API integration."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE = "https://www.googleapis.com/drive/v3"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    SCOPES = "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"

    def get_auth_url(self, state: str = "") -> str:
        params = {
            "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_DRIVE_REDIRECT_URI,
            "response_type": "code",
            "scope": self.SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data={
                "code": code,
                "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_DRIVE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
        if response.status_code != 200:
            raise Exception(f"Google Drive token exchange failed: {response.text}")
        return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data={
                "refresh_token": refresh_token,
                "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            })
        if response.status_code != 200:
            raise Exception(f"Google Drive token refresh failed: {response.text}")
        return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code != 200:
            raise Exception("Failed to get Google user info")
        return response.json()

    async def list_files(self, access_token: str, folder_id: str | None = None, page_token: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "pageSize": "50",
            "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, thumbnailLink, webViewLink)",
            "orderBy": "modifiedTime desc",
        }
        if folder_id:
            params["q"] = f"'{folder_id}' in parents and trashed = false"
        else:
            params["q"] = "trashed = false and (mimeType = 'application/pdf' or mimeType contains 'image/' or mimeType = 'text/csv' or mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')"
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/files", headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to list Google Drive files: {response.text}")
        return response.json()

    async def list_folders(self, access_token: str) -> list:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "q": "mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            "fields": "files(id, name, modifiedTime)",
            "orderBy": "name",
            "pageSize": "100",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/files", headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to list folders: {response.text}")
        return response.json().get("files", [])

    async def download_file(self, access_token: str, file_id: str) -> bytes:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/files/{file_id}?alt=media", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")
        return response.content

    async def upload_file(self, access_token: str, file_name: str, content: bytes, mime_type: str, folder_id: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        metadata = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        import json
        boundary = "fiscalflow_boundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--".encode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers={**headers, "Content-Type": f"multipart/related; boundary={boundary}"},
                content=body,
            )
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to upload file: {response.text}")
        return response.json()


class DropboxService:
    """Dropbox API integration."""

    AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
    TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
    API_BASE = "https://api.dropboxapi.com/2"
    CONTENT_BASE = "https://content.dropboxapi.com/2"

    def get_auth_url(self, state: str = "") -> str:
        params = {
            "client_id": settings.DROPBOX_APP_KEY,
            "redirect_uri": settings.DROPBOX_REDIRECT_URI,
            "response_type": "code",
            "token_access_type": "offline",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data={
                "code": code,
                "grant_type": "authorization_code",
                "client_id": settings.DROPBOX_APP_KEY,
                "client_secret": settings.DROPBOX_APP_SECRET,
                "redirect_uri": settings.DROPBOX_REDIRECT_URI,
            })
        if response.status_code != 200:
            raise Exception(f"Dropbox token exchange failed: {response.text}")
        return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data={
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "client_id": settings.DROPBOX_APP_KEY,
                "client_secret": settings.DROPBOX_APP_SECRET,
            })
        if response.status_code != 200:
            raise Exception(f"Dropbox token refresh failed: {response.text}")
        return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.API_BASE}/users/get_current_account", headers=headers, content="null")
        if response.status_code != 200:
            raise Exception("Failed to get Dropbox user info")
        data = response.json()
        return {
            "id": data.get("account_id"),
            "email": data.get("email"),
            "name": data.get("name", {}).get("display_name", ""),
        }

    async def list_files(self, access_token: str, path: str = "", cursor: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        if cursor:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.API_BASE}/files/list_folder/continue", headers=headers, json={"cursor": cursor})
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.API_BASE}/files/list_folder", headers=headers, json={
                    "path": path or "",
                    "recursive": False,
                    "include_media_info": False,
                    "include_deleted": False,
                    "limit": 50,
                })

        if response.status_code != 200:
            raise Exception(f"Failed to list Dropbox files: {response.text}")

        data = response.json()
        files = []
        for entry in data.get("entries", []):
            files.append({
                "id": entry.get("id"),
                "name": entry.get("name"),
                "path": entry.get("path_display"),
                "type": entry.get(".tag"),  # file or folder
                "size": entry.get("size"),
                "modified": entry.get("server_modified"),
            })

        return {
            "files": files,
            "cursor": data.get("cursor"),
            "has_more": data.get("has_more", False),
        }

    async def list_folders(self, access_token: str, path: str = "") -> list:
        result = await self.list_files(access_token, path)
        return [f for f in result["files"] if f["type"] == "folder"]

    async def download_file(self, access_token: str, path: str) -> bytes:
        import json
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": json.dumps({"path": path}),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.CONTENT_BASE}/files/download", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download Dropbox file: {response.text}")
        return response.content

    async def upload_file(self, access_token: str, path: str, content: bytes) -> dict:
        import json
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": json.dumps({"path": path, "mode": "add", "autorename": True}),
            "Content-Type": "application/octet-stream",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.CONTENT_BASE}/files/upload", headers=headers, content=content)
        if response.status_code != 200:
            raise Exception(f"Failed to upload to Dropbox: {response.text}")
        return response.json()


class OneDriveService:
    """Microsoft OneDrive API integration."""

    AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    API_BASE = "https://graph.microsoft.com/v1.0"
    SCOPES = "Files.ReadWrite.All User.Read offline_access"

    def get_auth_url(self, state: str = "") -> str:
        tenant = settings.ONEDRIVE_TENANT_ID or "common"
        params = {
            "client_id": settings.ONEDRIVE_CLIENT_ID,
            "redirect_uri": settings.ONEDRIVE_REDIRECT_URI,
            "response_type": "code",
            "scope": self.SCOPES,
            "state": state,
        }
        return f"{self.AUTH_URL.format(tenant=tenant)}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        tenant = settings.ONEDRIVE_TENANT_ID or "common"
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL.format(tenant=tenant), data={
                "code": code,
                "client_id": settings.ONEDRIVE_CLIENT_ID,
                "client_secret": settings.ONEDRIVE_CLIENT_SECRET,
                "redirect_uri": settings.ONEDRIVE_REDIRECT_URI,
                "grant_type": "authorization_code",
                "scope": self.SCOPES,
            })
        if response.status_code != 200:
            raise Exception(f"OneDrive token exchange failed: {response.text}")
        return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        tenant = settings.ONEDRIVE_TENANT_ID or "common"
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL.format(tenant=tenant), data={
                "refresh_token": refresh_token,
                "client_id": settings.ONEDRIVE_CLIENT_ID,
                "client_secret": settings.ONEDRIVE_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "scope": self.SCOPES,
            })
        if response.status_code != 200:
            raise Exception(f"OneDrive token refresh failed: {response.text}")
        return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/me", headers=headers)
        if response.status_code != 200:
            raise Exception("Failed to get OneDrive user info")
        data = response.json()
        return {
            "id": data.get("id"),
            "email": data.get("mail") or data.get("userPrincipalName"),
            "name": data.get("displayName"),
        }

    async def list_files(self, access_token: str, folder_id: str | None = None, skip_token: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}

        if folder_id:
            url = f"{self.API_BASE}/me/drive/items/{folder_id}/children"
        else:
            url = f"{self.API_BASE}/me/drive/root/children"

        params = {"$top": "50", "$orderby": "lastModifiedDateTime desc"}
        if skip_token:
            params["$skiptoken"] = skip_token

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to list OneDrive files: {response.text}")

        data = response.json()
        files = []
        for item in data.get("value", []):
            files.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "type": "folder" if "folder" in item else "file",
                "size": item.get("size"),
                "modified": item.get("lastModifiedDateTime"),
                "mime_type": item.get("file", {}).get("mimeType"),
                "web_url": item.get("webUrl"),
            })

        next_link = data.get("@odata.nextLink")
        return {"files": files, "next_link": next_link}

    async def list_folders(self, access_token: str, folder_id: str | None = None) -> list:
        result = await self.list_files(access_token, folder_id)
        return [f for f in result["files"] if f["type"] == "folder"]

    async def download_file(self, access_token: str, file_id: str) -> bytes:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/me/drive/items/{file_id}/content", headers=headers, follow_redirects=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download OneDrive file: {response.text}")
        return response.content

    async def upload_file(self, access_token: str, folder_id: str | None, file_name: str, content: bytes) -> dict:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/octet-stream"}

        if folder_id:
            url = f"{self.API_BASE}/me/drive/items/{folder_id}:/{file_name}:/content"
        else:
            url = f"{self.API_BASE}/me/drive/root:/{file_name}:/content"

        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, content=content)
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to upload to OneDrive: {response.text}")
        return response.json()


# Singleton instances
google_drive_service = GoogleDriveService()
dropbox_service = DropboxService()
onedrive_service = OneDriveService()
