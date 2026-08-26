def candidate_is_structurally_distinct(a, b):
    keys = ("layout_topology", "primitive_family", "hero_asset_strategy", "transition_mechanism")
    return sum(a.get(k) != b.get(k) for k in keys) >= 2


def tournament_has_required_diversity(candidates):
    primitive_families = {c.get("primitive_family") for c in candidates}
    layouts = {c.get("layout_topology") for c in candidates}
    return len(candidates) >= 4 and len(primitive_families) >= 3 and len(layouts) >= 2


def test_structural_candidate_contract():
    a = {"layout_topology":"editorial", "primitive_family":"occlusion", "hero_asset_strategy":"macro", "transition_mechanism":"foreground_pass"}
    b = {"layout_topology":"radial", "primitive_family":"depth_tunnel", "hero_asset_strategy":"replace", "transition_mechanism":"match_motion"}
    assert candidate_is_structurally_distinct(a, b)


def test_tournament_requires_search_radius():
    candidates = [
        {"layout_topology":"editorial", "primitive_family":"occlusion"},
        {"layout_topology":"radial", "primitive_family":"depth_tunnel"},
        {"layout_topology":"split", "primitive_family":"kinetic_type"},
        {"layout_topology":"editorial", "primitive_family":"occlusion"},
    ]
    assert tournament_has_required_diversity(candidates)
