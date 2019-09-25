class CantSolveDependencies(Exception):
    pass


def resolve_dependency_order(dependency_graph):
    """Function that return a ordered list of dependencies based in the dependency graph.

    Args:
        dependency_graph (dict): Dict that represent dependency graph,
        example a -> b -> c = {"a": ["b"], "b": ["c"], "c":[]}.

    Returns:
        list: Ordered dependencies.
    """
    ordered_deps = []
    number_of_nodes = len(dependency_graph.keys())
    solved_something = True
    while len(ordered_deps) < number_of_nodes and solved_something:
        solved_something = False
        for node, dependencies in dependency_graph.items():
            if not dependencies and node not in ordered_deps:
                _resolve_one(node, dependency_graph)
                ordered_deps.append(node)
                solved_something = True

    if len(ordered_deps) == number_of_nodes:
        return ordered_deps
    else:
        raise CantSolveDependencies(f"Unsolved graph: {dependency_graph}")


def _resolve_one(node, dependency_graph):
    for dependencies in dependency_graph.values():
        try:
            dependencies.remove(node)
        except Exception:
            pass
