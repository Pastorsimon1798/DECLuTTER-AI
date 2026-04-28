"""Algorithmic trade matching: find multi-party trade loops.

Core algorithm:
1. Build a want-graph from listings where edges represent
   "user A wants an item owned by user B".
2. Find cycles using DFS up to a configurable max length.
3. Prioritize shortest cycles (2-party first, then 3-party, etc.).
4. Score cycles by value match closeness.
"""

from __future__ import annotations

from typing import Any


def build_want_graph(listings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build adjacency list: user_id -> list of listings they want.

    A user "wants" a listing if:
    - The listing's item_label matches something in their wants_in_return, OR
    - The listing's tags overlap with their wants_in_return.
    """
    graph: dict[str, list[dict[str, Any]]] = {}

    for listing in listings:
        owner = listing["user_id"]
        if owner not in graph:
            graph[owner] = []

    for user_listing in listings:
        wanter = user_listing["user_id"]
        wants = set(w.lower() for w in user_listing.get("wants_in_return", []))
        tags = set(t.lower() for t in user_listing.get("tags", []))

        for target in listings:
            if target["user_id"] == wanter:
                continue
            target_label = target["item_label"].lower()
            target_tags = set(t.lower() for t in target.get("tags", []))

            if target_label in wants or target_tags & wants:
                graph.setdefault(wanter, []).append(target)

    return graph


def find_cycles(
    graph: dict[str, list[dict[str, Any]]],
    max_length: int = 4,
) -> list[list[dict[str, Any]]]:
    """Find all trade cycles up to max_length using DFS.

    Returns cycles as lists of listings, where each listing's owner
    wants the next listing in the cycle.
    """
    cycles: list[list[dict[str, Any]]] = []
    visited: set[str] = set()

    def dfs(
        start_user: str,
        current_user: str,
        path: list[dict[str, Any]],
        depth: int,
    ) -> None:
        if depth > max_length:
            return

        for listing in graph.get(current_user, []):
            next_user = listing["user_id"]

            if next_user == start_user and len(path) >= 1:
                cycles.append(path[:] + [listing])
                continue

            if next_user in visited:
                continue

            visited.add(next_user)
            path.append(listing)
            dfs(start_user, next_user, path, depth + 1)
            path.pop()
            visited.remove(next_user)

    for user in graph:
        visited.add(user)
        dfs(user, user, [], 1)
        visited.remove(user)

    # Remove duplicates (same cycle starting from different nodes)
    unique: set[tuple[str, ...]] = set()
    result: list[list[dict[str, Any]]] = []
    for cycle in cycles:
        # Normalize cycle by rotating to start with smallest user_id
        user_ids = [listing["user_id"] for listing in cycle]
        min_idx = user_ids.index(min(user_ids))
        normalized = tuple(user_ids[min_idx:] + user_ids[:min_idx])
        if normalized not in unique:
            unique.add(normalized)
            result.append(cycle)

    # Sort by cycle length (shortest first), then by value match score
    result.sort(key=lambda c: (len(c), -_cycle_score(c)))
    return result


def _cycle_score(cycle: list[dict[str, Any]]) -> float:
    """Score a cycle by how closely trade values match.

    Higher score = better value match across all parties.
    """
    if len(cycle) < 2:
        return 0.0

    values = [listing["trade_value_credits"] for listing in cycle]
    avg = sum(values) / len(values)
    variance = sum((v - avg) ** 2 for v in values) / len(values)
    # Lower variance = higher score
    return max(0.0, 100.0 - variance)


def find_trade_loops(
    listings: list[dict[str, Any]],
    max_length: int = 4,
) -> list[dict[str, Any]]:
    """High-level API: find trade loops from a list of listings.

    Returns structured results with participant info and scores.
    """
    graph = build_want_graph(listings)
    cycles = find_cycles(graph, max_length=max_length)

    results: list[dict[str, Any]] = []
    for cycle in cycles:
        user_ids = [listing["user_id"] for listing in cycle]
        results.append({
            "participants": user_ids,
            "listings": [listing["id"] for listing in cycle],
            "cycle_length": len(cycle),
            "score": round(_cycle_score(cycle), 2),
            "description": _describe_cycle(cycle),
        })

    return results


def _describe_cycle(cycle: list[dict[str, Any]]) -> str:
    """Generate a human-readable description of a trade cycle."""
    if len(cycle) == 2:
        return (
            f"Direct trade: {cycle[0]['user_id']} wants {cycle[1]['item_label']} "
            f"from {cycle[1]['user_id']}, who wants {cycle[0]['item_label']}"
        )

    parts = []
    for i, listing in enumerate(cycle):
        next_listing = cycle[(i + 1) % len(cycle)]
        parts.append(
            f"{listing['user_id']} → {next_listing['item_label']}"
        )
    return "Multi-party trade: " + " → ".join(parts)
