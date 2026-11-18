
import random
import pytest

from core import data, config
from core.rules import rules_errors, gap_conflict_count
from core.scoring import score

from algorithms import genetic


# ==================================================
# FIXTURES - ΚΟΙΝΗ ΠΡΟΕΤΟΙΜΑΣΙΑ
# ==================================================

@pytest.fixture(scope="module")
def ga_data():

    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    return True


@pytest.fixture
def random_schedule(ga_data):

    random.seed(42)

    return [
        genetic.random_day()
        for _ in config.R
    ]


# ==================================================
# 1. ΕΠΙΔΙΟΡΘΩΣΗ ΗΜΕΡΗΣΙΑΣ ΒΑΡΔΙΑΣ
# ==================================================

def test_repair_assigns_valid_roles(ga_data):

    random.seed(42)

    day = {
        "crew": random.sample(data.names, config.CREW),
        "duty": None,
        "mech": None,
        "elec": None
    }

    result = genetic.repair(day)

    assert result["mech"] in data.MECH
    assert result["elec"] in data.ELEC
    assert result["duty"] in data.DUTY_OK

    assert result["mech"] != result["elec"]

    assert result["mech"] in result["crew"]
    assert result["elec"] in result["crew"]
    assert result["duty"] in result["crew"]


def test_random_day_has_correct_structure(ga_data):

    random.seed(42)

    day = genetic.random_day()

    assert len(day["crew"]) == config.CREW

    assert day["mech"] in day["crew"]
    assert day["elec"] in day["crew"]
    assert day["duty"] in day["crew"]

    assert day["mech"] != day["elec"]


# ==================================================
# 2. ΑΝΤΙΓΡΑΦΗ ΠΡΟΓΡΑΜΜΑΤΩΝ
# ==================================================

def test_copy_day_creates_independent_copy(ga_data):

    day = genetic.random_day()
    copied = genetic.copy_day(day)

    assert copied == day
    assert copied is not day
    assert copied["crew"] is not day["crew"]


def test_copy_schedule_creates_independent_copy(random_schedule):

    copied = genetic.copy_sched(random_schedule)

    assert copied == random_schedule
    assert copied is not random_schedule

    assert copied[0] is not random_schedule[0]
    assert copied[0]["crew"] is not random_schedule[0]["crew"]


# ==================================================
# 3. CROSSOVER - ΔΙΑΣΤΑΥΡΩΣΗ
# ==================================================

def test_crossover_returns_correct_schedule(random_schedule):

    random.seed(42)

    parent_a = genetic.copy_sched(random_schedule)
    parent_b = genetic.copy_sched(random_schedule)

    child = genetic.crossover(parent_a, parent_b)

    assert len(child) == len(config.R)

    for day in child:

        assert len(day["crew"]) == config.CREW

        assert day["mech"] in day["crew"]
        assert day["elec"] in day["crew"]
        assert day["duty"] in day["crew"]


def test_crossover_does_not_modify_parents(random_schedule):

    random.seed(42)

    parent_a = genetic.copy_sched(random_schedule)
    parent_b = genetic.copy_sched(random_schedule)

    original_a = genetic.copy_sched(parent_a)
    original_b = genetic.copy_sched(parent_b)

    genetic.crossover(parent_a, parent_b)

    assert parent_a == original_a
    assert parent_b == original_b


# ==================================================
# 4. ΕΛΕΓΧΟΣ ΔΥΝΑΤΟΤΗΤΑΣ ΑΝΑΘΕΣΗΣ
# ==================================================

def test_can_assign_respects_minimum_gap(ga_data):

    sched = [
        {
            "crew": [],
            "duty": None,
            "mech": None,
            "elec": None
        }
        for _ in config.R
    ]

    member = data.names[0]

    sched[0]["crew"].append(member)

    assert not genetic.can_assign(
        member,
        config.MIN_GAP - 1,
        sched
    )

    assert genetic.can_assign(
        member,
        config.MIN_GAP,
        sched
    )


# ==================================================
# 5. ΑΝΤΙΚΑΤΑΣΤΑΣΗ ΜΕΛΟΥΣ ΚΑΙ ΡΟΛΩΝ
# ==================================================

def test_replacement_preserves_valid_roles(ga_data):

    random.seed(42)

    day = genetic.random_day()

    old_member = day["mech"]

    candidates = [
        m for m in data.MECH
        if m not in day["crew"]
        and m != day["elec"]
    ]

    if not candidates:
        pytest.skip("Δεν υπάρχει διαθέσιμος μηχανικός.")

    new_member = candidates[0]

    index = day["crew"].index(old_member)
    day["crew"][index] = new_member

    result = genetic.replacement_preserves_roles(
        day,
        old_member,
        new_member
    )

    assert result is True

    assert day["mech"] == new_member
    assert day["mech"] in day["crew"]
    assert day["elec"] in day["crew"]

    assert day["mech"] != day["elec"]


def test_replacement_rejects_unqualified_member(ga_data):

    random.seed(42)

    day = genetic.random_day()

    old_member = day["mech"]

    candidates = [
        m for m in data.names
        if m not in data.MECH
        and m not in day["crew"]
    ]

    if not candidates:
        pytest.skip("Δεν υπάρχει μη επιλέξιμο μέλος.")

    new_member = candidates[0]

    original_mech = day["mech"]

    result = genetic.replacement_preserves_roles(
        day,
        old_member,
        new_member
    )

    assert result is False
    assert day["mech"] == original_mech


# ==================================================
# 6. ΕΠΙΔΙΟΡΘΩΣΗ ΣΥΝΟΛΙΚΟΥ ΠΡΟΓΡΑΜΜΑΤΟΣ
# ==================================================

def test_repair_schedule_returns_original_object(random_schedule):

    original_id = id(random_schedule)

    result = genetic.repair_schedule(random_schedule)

    assert id(result) == original_id


def test_repair_schedule_does_not_increase_gap_conflicts(
    random_schedule
):

    before = gap_conflict_count(random_schedule)

    repaired = genetic.repair_schedule(random_schedule)

    after = gap_conflict_count(repaired)

    assert after <= before


# ==================================================
# 7. MUTATION - ΜΕΤΑΛΛΑΞΗ
# ==================================================

def test_mutation_returns_schedule(random_schedule):

    random.seed(42)

    result = genetic.mutate(
        random_schedule,
        rate=0
    )

    assert result is random_schedule
    assert len(result) == config.DAYS


def test_mutation_preserves_daily_role_assignments(random_schedule):

    random.seed(42)

    result = genetic.mutate(
        random_schedule,
        rate=1
    )

    for day in result:

        assert len(day["crew"]) == config.CREW

        assert day["mech"] in data.MECH
        assert day["elec"] in data.ELEC
        assert day["duty"] in data.DUTY_OK

        assert day["mech"] in day["crew"]
        assert day["elec"] in day["crew"]
        assert day["duty"] in day["crew"]

        assert day["mech"] != day["elec"]


# ==================================================
# 8. LOCAL SEARCH - ΤΟΠΙΚΗ ΑΝΑΖΗΤΗΣΗ
# ==================================================

def test_local_search_returns_valid_result(random_schedule):

    random.seed(42)

    result, result_score = genetic.local_search(
        random_schedule,
        passes=1
    )

    assert len(result) == config.DAYS
    assert result_score == score(result)

    assert rules_errors(result) == []


# ==================================================
# 9. GENETIC ALGORITHM - ΣΥΝΟΛΙΚΗ ΕΚΤΕΛΕΣΗ
# ==================================================


def test_evolve_ga_returns_valid_result(ga_data, monkeypatch):

    random.seed(42)

    # Μικρός πληθυσμός και λίγες γενιές για το test.
    monkeypatch.setattr(config, "GA_POP", 10)
    monkeypatch.setattr(config, "GA_GENS", 2)
    monkeypatch.setattr(config, "GA_PATIENCE", 3)

    # Κρατάμε την πραγματική local_search,
    # αλλά περιορίζουμε τις επαναλήψεις της.
    original_local_search = genetic.local_search

    monkeypatch.setattr(
        genetic,
        "local_search",
        lambda sched: original_local_search(sched, passes=1)
    )

    result, result_score = genetic.evolve_ga()

    assert len(result) == config.DAYS

    assert isinstance(result_score, tuple)
    assert len(result_score) == 8

    assert result_score == score(result)

    assert rules_errors(result) == []
