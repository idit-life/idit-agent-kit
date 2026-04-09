"""
IditAgent — the one class you need.
"""

import httpx


class IditAgent:
    """
    A minimal client for AI agents to mint entries to a Personal Idit chain.

    Args:
        signer: Name of the signing key on the Idit server (e.g., "my-agent").
                The key must already exist — run `idit init my-agent` on the server first.
        server: Idit server URL. Default: http://localhost:18793
        model: Model identifier (e.g., "gpt-4o", "claude-opus-4-6", "llama3.3:70b").
               Stored in chain metadata so you always know what model signed what.
        node: Node identifier. Default: "local"
        timeout: HTTP timeout in seconds. Default: 30
        api_key: Optional API key for authenticated servers (IDIT_API_KEY).
                 Sent as X-API-Key header on all requests.
    """

    def __init__(
        self,
        signer: str,
        server: str = "http://localhost:18793",
        model: str = "",
        node: str = "local",
        timeout: float = 30,
        api_key: str = "",
    ):
        self.signer = signer
        self.server = server.rstrip("/")
        self.model = model
        self.node = node
        self._api_key = api_key
        headers = {"X-API-Key": api_key} if api_key else {}
        self.client = httpx.Client(base_url=self.server, timeout=timeout, headers=headers)

    def mint(
        self,
        content: str,
        entry_type: str = "note",
        description: str = "",
        tags: list[str] | None = None,
        opens_at: str = "",
        confidential: bool = False,
        sealed_ref: str = "",
    ) -> dict:
        """
        Mint a new entry to the chain.

        Args:
            content: The text content to record.
            entry_type: Category — "note", "memory", "decision", "milestone",
                        "document", "letter", "feeling", "morning_report",
                        "battle_plan", "seal", etc.
            description: Short description (shows in timeline).
            tags: Optional list of tags.
            opens_at: ISO date string for timelock (e.g., "2036-01-01"). Empty = no lock.
            confidential: If True, auto-timelock (viewer handles display).
            sealed_ref: Entry ID to seal after the fact.

        Returns:
            Dict with entry_id, entry_hash, signature, created_at, etc.
        """
        payload = {
            "content": content,
            "signer": self.signer,
            "model": self.model,
            "node": self.node,
            "entry_type": entry_type,
            "description": description,
            "tags": tags or [],
            "opens_at": opens_at,
            "confidential": confidential,
            "sealed_ref": sealed_ref,
        }
        r = self.client.post("/mint", json=payload)
        r.raise_for_status()
        return r.json()

    def note(self, content: str, description: str = "") -> dict:
        """Mint a note."""
        return self.mint(content, entry_type="note", description=description)

    def memory(self, content: str, description: str = "") -> dict:
        """Mint a memory."""
        return self.mint(content, entry_type="memory", description=description)

    def decision(self, content: str, description: str = "") -> dict:
        """Mint a decision."""
        return self.mint(content, entry_type="decision", description=description)

    def milestone(self, content: str, description: str = "") -> dict:
        """Mint a milestone."""
        return self.mint(content, entry_type="milestone", description=description)

    def log(self, content: str, description: str = "") -> dict:
        """Mint a log entry (alias for morning reports, daily logs, etc.)."""
        return self.mint(content, entry_type="log", description=description)

    def feel(self, content: str, description: str = "") -> dict:
        """Mint a feeling entry."""
        return self.mint(content, entry_type="feeling", description=description)

    def letter(
        self, content: str, description: str = "", opens_at: str = "",
    ) -> dict:
        """
        Mint a letter, optionally timelocked.

        Args:
            content: The letter text.
            description: Short description.
            opens_at: ISO date when the letter can be read (e.g., "2036-01-01").
                      Empty string means no timelock.
        """
        return self.mint(
            content, entry_type="letter", description=description,
            opens_at=opens_at, confidential=bool(opens_at),
        )

    def seal(
        self, entry_id: str, opens_at: str = "", description: str = "",
    ) -> dict:
        """
        Seal an existing entry by minting a seal reference.

        Args:
            entry_id: The entry ID to seal (e.g., "id-abc123...").
            opens_at: ISO date when the seal opens (e.g., "2101-01-01").
            description: Optional description.
        """
        content = f"SEAL: Entry {entry_id} sealed by {self.signer}."
        if opens_at:
            content += f" Opens at {opens_at}."
        return self.mint(
            content, entry_type="seal",
            description=description or f"Seal of {entry_id}",
            opens_at=opens_at, confidential=True, sealed_ref=entry_id,
        )

    def status(self) -> dict:
        """Get chain stats."""
        r = self.client.get("/chain/stats")
        r.raise_for_status()
        return r.json()

    def verify(self) -> dict:
        """Verify chain integrity. Returns {valid: bool, length: int, errors: [...]}."""
        r = self.client.get("/chain/verify")
        r.raise_for_status()
        return r.json()

    def health(self) -> dict:
        """Check if the server is reachable."""
        r = self.client.get("/health")
        r.raise_for_status()
        return r.json()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
