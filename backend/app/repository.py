from functools import cached_property
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from supabase import Client, create_client

from app.config import Settings


class ConnectionRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def client(self) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_service_key:
            raise RuntimeError("Supabase is not configured")
        return create_client(self.settings.supabase_url, self.settings.supabase_service_key)

    @cached_property
    def cipher(self) -> Fernet:
        if not self.settings.token_encryption_key:
            raise RuntimeError("Token encryption is not configured")
        try:
            return Fernet(self.settings.token_encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as error:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY is invalid") from error

    def encrypt_token(self, value: str) -> str:
        return self.cipher.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt_token(self, value: str) -> str:
        if not value.startswith("gAAAA"):
            return value
        try:
            return self.cipher.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken as error:
            raise RuntimeError("Stored Gmail credentials could not be decrypted") from error

    def upsert_user(self, email: str) -> dict[str, Any]:
        result = self.client.table("users").upsert({"email": email}, on_conflict="email").execute()
        if not result.data:
            raise RuntimeError("Could not store the connected account")
        return result.data[0]

    def save_connection(self, user_id: str, email: str, credentials: Any) -> None:
        payload = {
            "user_id": user_id,
            "gmail_address": email,
            "access_token": self.encrypt_token(credentials.token or ""),
            "refresh_token": self.encrypt_token(credentials.refresh_token or ""),
            "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        self.client.table("gmail_connections").upsert(payload, on_conflict="user_id").execute()

    def get_connection(self, user_id: str) -> dict[str, Any] | None:
        result = self.client.table("gmail_connections").select("*").eq("user_id", user_id).limit(1).execute()
        if not result.data:
            return None
        connection = result.data[0]
        connection["access_token"] = self.decrypt_token(connection.get("access_token") or "")
        connection["refresh_token"] = self.decrypt_token(connection.get("refresh_token") or "")
        return connection

    def update_access_token(self, user_id: str, token: str, expiry: str | None) -> None:
        (
            self.client.table("gmail_connections")
            .update({"access_token": self.encrypt_token(token), "token_expiry": expiry})
            .eq("user_id", user_id)
            .execute()
        )

    def create_knowledge_document(
        self,
        user_id: str,
        title: str,
        source_url: str | None,
        chunks: list[tuple[str, list[float]]],
    ) -> dict[str, Any]:
        document_result = (
            self.client.table("knowledge_documents")
            .insert({"user_id": user_id, "title": title, "source_url": source_url})
            .execute()
        )
        if not document_result.data:
            raise RuntimeError("Could not create the knowledge document")
        document = document_result.data[0]
        try:
            chunk_result = (
                self.client.table("knowledge_chunks")
                .insert(
                    [
                        {
                            "document_id": document["id"],
                            "user_id": user_id,
                            "chunk_index": index,
                            "content": content,
                            "embedding": embedding,
                        }
                        for index, (content, embedding) in enumerate(chunks)
                    ]
                )
                .execute()
            )
            if len(chunk_result.data or []) != len(chunks):
                raise RuntimeError("Could not store every knowledge chunk")
        except Exception:
            self.client.table("knowledge_documents").delete().eq("id", document["id"]).execute()
            raise
        document["chunk_count"] = len(chunks)
        return document

    def list_knowledge_documents(self, user_id: str) -> list[dict[str, Any]]:
        result = self.client.rpc("list_knowledge_documents", {"p_user_id": user_id}).execute()
        return list(result.data or [])

    def delete_knowledge_document(self, user_id: str, document_id: UUID) -> bool:
        result = (
            self.client.table("knowledge_documents")
            .delete()
            .eq("id", str(document_id))
            .eq("user_id", user_id)
            .execute()
        )
        return bool(result.data)

    def search_knowledge(
        self,
        user_id: str,
        embedding: list[float],
        threshold: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        result = self.client.rpc(
            "match_knowledge_chunks",
            {
                "p_user_id": user_id,
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": limit,
            },
        ).execute()
        return list(result.data or [])
