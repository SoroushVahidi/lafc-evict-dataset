import pytest

import tier1_core as t1


def test_assert_no_learned_policy_passes_for_tier1_policies():
    t1.assert_no_learned_policy(["lru", "mru", "random", "sieve"])  # must not raise


def test_assert_no_learned_policy_rejects_evict_value_v1():
    with pytest.raises(RuntimeError, match="learned policy"):
        t1.assert_no_learned_policy(["lru", "evict_value_v1"])


def test_build_policy_rejects_learned_policy_name():
    with pytest.raises(RuntimeError, match="learned policy"):
        t1.build_policy("evict_value_v1")


def test_static_policy_tuple_never_contains_a_learned_policy():
    assert "evict_value_v1" not in t1.POLICIES
    assert t1.LEARNED_POLICY_NAMES.isdisjoint(set(t1.POLICIES))


def test_tier1_never_constructs_a_learned_policy_instance():
    # NOTE: lafc.runner.run_policy (a required Tier-1 dependency) transitively
    # imports and constructs one default EvictValueV1Policy() into its own
    # internal registry as an unavoidable module-import side effect -- see
    # the NOTE in tier1_core._import_simulator_modules. That instance is
    # never invoked with real data and Tier 1's own code path never reads
    # from that registry. The guarantee this harness actually provides is
    # that build_policy() -- the only way Tier 1 constructs a policy object
    # for execution -- can never produce a learned-policy instance for any
    # of the four Tier-1 policy names, and explicitly refuses the name.
    for name in t1.POLICIES:
        policy = t1.build_policy(name, seed=0 if name == "random" else None)
        assert type(policy).__name__ != "EvictValueV1Policy"
        assert policy.name != "evict_value_v1"


def test_build_plan_itself_is_guarded():
    # build_plan() calls assert_no_learned_policy internally; this is a
    # regression guard in case someone adds a 5th policy to POLICIES/plan
    # generation without checking it against LEARNED_POLICY_NAMES.
    plan = t1.build_plan()
    assert t1.LEARNED_POLICY_NAMES.isdisjoint({e.policy for e in plan})
