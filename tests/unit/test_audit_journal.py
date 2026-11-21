"""Unit tests for cryptographic audit journal and tampering detection."""

from forge.persistence.audit_journal import AuditJournal


def test_audit_journal_integrity(temp_db):
    journal = AuditJournal(temp_db)

    # Record 3 events
    journal.record_event("action.1", "target.1", "success", "corr_1")
    journal.record_event("action.2", "target.2", "success", "corr_2")
    journal.record_event("action.3", "target.3", "denied", "corr_3")

    # Verify chain
    is_valid, msg, broken_id = journal.verify_integrity()
    assert is_valid is True
    assert broken_id is None


def test_audit_journal_tampering_detection(temp_db):
    journal = AuditJournal(temp_db)

    # Record events
    journal.record_event("tool.exec", "tool_a", "success", "corr_1")
    journal.record_event("tool.exec", "tool_b", "success", "corr_2")

    # Tamper with an event record in SQLite directly
    with journal.mgr.get_connection() as conn:
        conn.execute("UPDATE audit_events SET outcome = 'tampered' WHERE id = 1;")

    # Verify detection
    is_valid, msg, broken_id = journal.verify_integrity()
    assert is_valid is False
    assert broken_id == 1
    assert "tampering detected" in msg.lower()
