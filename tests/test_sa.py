
import random
import pytest

from core import data, config
from core.rules import rules_errors
from core.scoring import score

from algorithms.simulated_annealing import (
    copy_day,
    copy_sched,
    create_initial_solution,
    create_neighbor,
    create_neighbor_smart,
    create_neighbor_swap,
    diagnose_invalid_rules,
    lexicographic_cost,
    accept_solution,
    cool_temperature,
    create_sa_stats,
    solve_sa
)


# ==================================================
# FIXTURES - ΚΟΙΝΗ ΠΡΟΕΤΟΙΜΑΣΙΑ
# ==================================================

@pytest.fixture(scope="module")
def sa_data():

    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    return True


@pytest.fixture(scope="module")
def initial_schedule(sa_data):

    rng = random.Random(42)

    return create_initial_solution(rng)


@pytest.fixture(scope="module")
def sa_result(sa_data):

    sched, sa_score = solve_sa(
        iterations_per_temp=10,
        max_levels=5,
        alpha=0.95,
        neighbor_fn=create_neighbor_smart,
        seed=42
    )

    return sched, sa_score


# ==================================================
# 1. ΑΡΧΙΚΗ ΛΥΣΗ
# ==================================================

def test_initial_solution_is_valid(initial_schedule):

    assert len(initial_schedule) == config.DAYS
    assert rules_errors(initial_schedule) == []


def test_initial_solution_has_correct_crew_size(initial_schedule):

    for day in initial_schedule:
        assert len(day["crew"]) == config.CREW


def test_initial_solution_is_reproducible(sa_data):

    rng1 = random.Random(42)
    rng2 = random.Random(42)

    sched1 = create_initial_solution(rng1)
    sched2 = create_initial_solution(rng2)

    assert sched1 == sched2


# ==================================================
# 2. ΑΝΤΙΓΡΑΦΗ ΛΥΣΕΩΝ
# ==================================================

def test_copy_day_creates_independent_copy(initial_schedule):

    original = initial_schedule[0]
    copied = copy_day(original)

    assert copied == original
    assert copied is not original
    assert copied["crew"] is not original["crew"]


def test_copy_schedule_creates_independent_copy(initial_schedule):

    copied = copy_sched(initial_schedule)

    assert copied == initial_schedule
    assert copied is not initial_schedule

    assert copied[0] is not initial_schedule[0]
    assert copied[0]["crew"] is not initial_schedule[0]["crew"]


# ==================================================
# 3. NEIGHBOR FUNCTIONS
# ==================================================

@pytest.mark.parametrize(
    "neighbor_fn",
    [
        create_neighbor,
        create_neighbor_smart,
        create_neighbor_swap
    ]
)
def test_neighbors_preserve_validity(initial_schedule, neighbor_fn):

    rng = random.Random(42)

    neighbor = neighbor_fn(
        initial_schedule,
        rng
    )

    assert rules_errors(neighbor) == []


def test_neighbors_do_not_modify_original(initial_schedule):

    original = copy_sched(initial_schedule)

    rng = random.Random(42)

    create_neighbor(initial_schedule, rng)
    create_neighbor_smart(initial_schedule, rng)
    create_neighbor_swap(initial_schedule, rng)

    assert initial_schedule == original


# ==================================================
# 4. ΔΙΑΓΝΩΣΗ ΠΑΡΑΒΙΑΣΕΩΝ
# ==================================================

def test_diagnose_invalid_rules_returns_empty_for_valid_schedule(
    initial_schedule
):

    assert diagnose_invalid_rules(initial_schedule) == []


# ==================================================
# 5. ΛΕΞΙΚΟΓΡΑΦΙΚΗ ΚΩΔΙΚΟΠΟΙΗΣΗ
# ==================================================

def test_lexicographic_cost_preserves_order(sa_data):

    better = (0, 0, 0, 0, 0, 0, 0, 0)
    worse = (0, 1, 0, 0, 0, 0, 0, 0)

    assert better < worse

    assert lexicographic_cost(better) < lexicographic_cost(worse)


def test_lexicographic_cost_rejects_hard_violations(sa_data):

    invalid_score = (1, 0, 0, 0, 0, 0, 0, 0)

    with pytest.raises(ValueError):
        lexicographic_cost(invalid_score)


# ==================================================
# 6. ΑΠΟΔΟΧΗ ΛΥΣΕΩΝ
# ==================================================

def test_accepts_better_solution(sa_data):

    current = (0, 1, 0, 0, 0, 0, 0, 0)
    better = (0, 0, 0, 0, 0, 0, 0, 0)

    rng = random.Random(42)

    assert accept_solution(current, better, 100, rng)


def test_accepts_equal_solution(sa_data):

    current = (0, 0, 0, 0, 0, 0, 0, 0)

    rng = random.Random(42)

    assert accept_solution(current, current, 100, rng)


def test_rejects_worse_solution_at_zero_temperature(sa_data):

    current = (0, 0, 0, 0, 0, 0, 0, 0)
    worse = (0, 1, 0, 0, 0, 0, 0, 0)

    rng = random.Random(42)

    assert not accept_solution(current, worse, 0, rng)


# ==================================================
# 7. ΘΕΡΜΟΚΡΑΣΙΑ
# ==================================================

def test_cool_temperature_reduces_temperature():

    initial_temperature = 100

    new_temperature = cool_temperature(
        initial_temperature,
        alpha=0.95
    )

    assert new_temperature == 95
    assert new_temperature < initial_temperature


# ==================================================
# 8. ΣΤΑΤΙΣΤΙΚΑ
# ==================================================

def test_create_sa_stats_initializes_counters():

    stats = create_sa_stats()

    assert stats["better_accepted"] == 0
    assert stats["worse_accepted"] == 0
    assert stats["rejected"] == 0
    assert stats["invalid"] == 0


# ==================================================
# 9. ΣΥΝΟΛΙΚΗ ΕΚΤΕΛΕΣΗ SA
# ==================================================

def test_sa_returns_valid_schedule(sa_result):

    sched, sa_score = sa_result

    assert len(sched) == config.DAYS
    assert rules_errors(sched) == []


def test_sa_returns_correct_score(sa_result):

    sched, sa_score = sa_result

    assert sa_score == score(sched)


def test_sa_returns_eight_score_criteria(sa_result):

    sched, sa_score = sa_result

    assert isinstance(sa_score, tuple)
    assert len(sa_score) == 8
