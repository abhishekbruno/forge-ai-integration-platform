"""Append-only tamper-evident audit journal with SHA-256 hash chaining."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge.domain.audit import AuditEvent
from forge.persistence.db import get_db_manager
from forge.security.hashes import canonical_json_dumps, compute_audit_hash

GENESIS_HASH = "0" * 64


class AuditJournal:
    """Manages recording and cryptographic verification of audit records."""

    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def record_event(
        self,
        action: str,
        target: str,
        outcome: str,
        correlation_id: str,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Append a new tamper-evident audit event."""
        if details is None:
            details = {}

        now_iso = datetime.now(timezone.utc).isoformat()

        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            try:
                # Retrieve latest event hash
                cursor.execute("SELECT id, event_hash FROM audit_events ORDER BY id DESC LIMIT 1;")
                row = cursor.fetchone()
                if row:
                    _prev_id, prev_hash = row["id"], row["event_hash"]
                else:
                    _prev_id, prev_hash = 0, GENESIS_HASH

                # Canonical payload for hashing
                payload = {
                    "timestamp": now_iso,
                    "actor": actor,
                    "action": action,
                    "target": target,
                    "outcome": outcome,
                    "correlation_id": correlation_id,
                    "details": details,
                }
                event_hash = compute_audit_hash(prev_hash, payload)

                cursor.execute(
                    """
                    INSERT INTO audit_events
                    (timestamp, actor, action, target, outcome, correlation_id, details_json, previous_hash, event_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        now_iso,
                        actor,
                        action,
                        target,
                        outcome,
                        correlation_id,
                        canonical_json_dumps(details),
                        prev_hash,
                        event_hash,
                    ),
                )
                new_id = cursor.lastrowid
                cursor.execute("COMMIT;")

                return AuditEvent(
                    id=new_id,
                    timestamp=now_iso,
                    actor=actor,
                    action=action,
                    target=target,
                    outcome=outcome,
                    correlation_id=correlation_id,
                    details=details,
                    previous_hash=prev_hash,
                    event_hash=event_hash,
                )
            except Exception:
                cursor.execute("ROLLBACK;")
                raise

    def list_events(
        self,
        limit: int = 100,
        action: str | None = None,
        correlation_id: str | None = None,
    ) -> list[AuditEvent]:
        """Retrieve audit events in descending chronological order."""
        with self.mgr.get_connection() as conn:
            query = "SELECT * FROM audit_events WHERE 1=1"
            params: list[Any] = []
            if action:
                query += " AND action = ?"
                params.append(action)
            if correlation_id:
                query += " AND correlation_id = ?"
                params.append(correlation_id)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            events = []
            for row in rows:
                events.append(
                    AuditEvent(
                        id=row["id"],
                        timestamp=row["timestamp"],
                        actor=row["actor"],
                        action=row["action"],
                        target=row["target"],
                        outcome=row["outcome"],
                        correlation_id=row["correlation_id"],
                        details=json.loads(row["details_json"]),
                        previous_hash=row["previous_hash"],
                        event_hash=row["event_hash"],
                    )
                )
            return events

    def verify_integrity(self) -> tuple[bool, str, int | None]:
        """Verify the cryptographic hash chain of the entire audit journal.

        Returns (is_valid, message, broken_record_id).
        """
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_events ORDER BY id ASC;")
            rows = cursor.fetchall()

            expected_prev_hash = GENESIS_HASH
            for row in rows:
                rec_id = row["id"]
                prev_hash = row["previous_hash"]
                event_hash = row["event_hash"]
                details = json.loads(row["details_json"])

                if prev_hash != expected_prev_hash:
                    return (
                        False,
                        f"Chain mismatch at record ID {rec_id}: expected previous hash {expected_prev_hash[:16]}..., got {prev_hash[:16]}...",
                        rec_id,
                    )

                payload = {
                    "timestamp": row["timestamp"],
                    "actor": row["actor"],
                    "action": row["action"],
                    "target": row["target"],
                    "outcome": row["outcome"],
                    "correlation_id": row["correlation_id"],
                    "details": details,
                }
                computed_hash = compute_audit_hash(prev_hash, payload)

                if computed_hash != event_hash:
                    return (
                        False,
                        f"Hash tampering detected at record ID {rec_id}: computed {computed_hash[:16]}..., stored {event_hash[:16]}...",
                        rec_id,
                    )

                expected_prev_hash = event_hash

            return (True, f"Audit journal integrity verified across {len(rows)} events.", None)
