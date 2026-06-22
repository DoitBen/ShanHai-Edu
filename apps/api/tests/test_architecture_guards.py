from app.store import ProjectStore


def test_project_store_does_not_expose_direct_approve_bypass():
    assert not hasattr(ProjectStore, "approve_node")
