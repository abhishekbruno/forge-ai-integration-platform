"""Unit tests for approval broker and single-use grants."""

from forge.core.approval_broker import ApprovalBroker
from forge.security.hashes import hash_arguments


def test_approval_grant_and_consume(temp_db):
    broker = ApprovalBroker(temp_db)
    args = {"item_id": "test_1", "name": "Item"}
    arg_hash = hash_arguments(args)

    # 1. Check no grant exists
    assert broker.check_and_consume_grant("test_tool", arg_hash) is False

    # 2. Grant approval
    grant = broker.grant_approval("test_tool", arg_hash, "corr_123", ttl_seconds=60)
    assert grant.consumed is False

    # 3. Consume once -> MUST succeed
    assert broker.check_and_consume_grant("test_tool", arg_hash) is True

    # 4. Consume second time -> MUST fail (single-use)
    assert broker.check_and_consume_grant("test_tool", arg_hash) is False
