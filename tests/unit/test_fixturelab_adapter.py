"""Unit tests for FixtureLab reference adapter."""

import pytest

from forge.adapters.fixturelab import FixtureLabAdapter
from forge.domain.errors import AdapterExecutionError


def test_fixturelab_full_lifecycle(temp_workspace):
    adapter = FixtureLabAdapter()

    # 1. Status initially empty
    st = adapter.invoke_capability("fixturelab.get_status", {}, temp_workspace)
    assert st["status"] == "ready"
    assert st["item_count"] == 0

    # 2. Create item
    res = adapter.invoke_capability(
        "fixturelab.create_item",
        {"item_id": "item_1", "name": "Item 1", "category": "alpha"},
        temp_workspace,
    )
    assert res["success"] is True
    assert res["created_id"] == "item_1"
    assert res["version"] == 1

    # 3. Read item
    get_res = adapter.invoke_capability(
        "fixturelab.get_item", {"item_id": "item_1"}, temp_workspace
    )
    assert get_res["item"]["name"] == "Item 1"

    # 4. Update item with version check
    up_res = adapter.invoke_capability(
        "fixturelab.update_item",
        {"item_id": "item_1", "expected_version": 1, "name": "Updated 1"},
        temp_workspace,
    )
    assert up_res["success"] is True
    assert up_res["new_version"] == 2

    # 5. Version conflict check
    with pytest.raises(AdapterExecutionError, match="Conflict"):
        adapter.invoke_capability(
            "fixturelab.update_item",
            {"item_id": "item_1", "expected_version": 1, "name": "Stale Update"},
            temp_workspace,
        )

    # 6. Delete item
    del_res = adapter.invoke_capability(
        "fixturelab.delete_item", {"item_id": "item_1"}, temp_workspace
    )
    assert del_res["success"] is True

    # 7. Verify deletion
    with pytest.raises(AdapterExecutionError, match="not found"):
        adapter.invoke_capability("fixturelab.get_item", {"item_id": "item_1"}, temp_workspace)
