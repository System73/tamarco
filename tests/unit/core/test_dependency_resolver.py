import pytest

from tamarco.core.dependency_resolver import CantSolveDependencies, resolve_dependency_order


def test_resolve_dependencies():
    dependency_graph = {
        "settings": [],
        "logging": ["settings"],
        "metrics": ["logging", "settings"],
        "status": ["logging", "settings"],
        "amqp": ["logging", "settings", "status"],
    }
    result = resolve_dependency_order(dependency_graph)

    assert result[0] == "settings"
    assert result[1] == "logging"

    assert "metrics" in result[2:4]
    assert "status" in result[2:4]

    assert result[-1] == "amqp"


def test_resolve_dependencies_fail():
    dependency_graph = {
        "settings": [],
        "logging": ["settings", "status"],
        "metrics": ["logging", "settings"],
        "status": ["logging", "settings"],
        "amqp": ["logging", "settings", "status"],
    }

    with pytest.raises(CantSolveDependencies):
        result = resolve_dependency_order(dependency_graph)
        assert result
