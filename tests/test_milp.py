
import pytest
import pulp

from core import data, config
from core.rules import rules_errors

from algorithms.milp import (
    MAX_LEVEL,
    create_decision_variables,
    add_basic_constraints,
    add_gap_constraints,
    add_over_constraints,
    add_coverage_constraints,
    run_stage,
    solve_milp
)


# ==================================================
# FIXTURES - ΚΟΙΝΗ ΠΡΟΕΤΟΙΜΑΣΙΑ
# ==================================================

@pytest.fixture(scope="module")
def milp_data():

    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    return True


@pytest.fixture(scope="module")
def milp_result(milp_data):

    sched, results = solve_milp()

    return sched, results


# ==================================================
# 1. ΜΕΤΑΒΛΗΤΕΣ ΑΠΟΦΑΣΗΣ
# ==================================================

def test_decision_variables_have_correct_dimensions(milp_data):

    model = pulp.LpProblem(
        "Test_MILP",
        pulp.LpMinimize
    )

    x, duty, mech, elec, over, lv, cov_h, cov_f = (
        create_decision_variables(model)
    )

    n = len(data.names)
    days = len(config.R)

    assert len(x) == n * days
    assert len(duty) == n * days
    assert len(mech) == n * days
    assert len(elec) == n * days

    assert len(over) == n
    assert len(lv) == n * MAX_LEVEL

    assert len(cov_h) == n
    assert len(cov_f) == n


def test_decision_variables_have_correct_bounds(milp_data):

    model = pulp.LpProblem(
        "Test_MILP_Bounds",
        pulp.LpMinimize
    )

    x, duty, mech, elec, over, lv, cov_h, cov_f = (
        create_decision_variables(model)
    )

    for variable in x.values():
        assert variable.lowBound == 0
        assert variable.upBound == 1

    for variable in over.values():
        assert variable.lowBound == 0
        assert variable.upBound == MAX_LEVEL


# ==================================================
# 2. ΠΕΡΙΟΡΙΣΜΟΙ MILP
# ==================================================

def test_constraint_functions_build_model(milp_data):

    model = pulp.LpProblem(
        "Test_MILP_Constraints",
        pulp.LpMinimize
    )

    x, duty, mech, elec, over, lv, cov_h, cov_f = (
        create_decision_variables(model)
    )

    add_basic_constraints(
        model, x, duty, mech, elec
    )

    add_gap_constraints(
        model, x
    )

    add_over_constraints(
        model, x, over, lv
    )

    add_coverage_constraints(
        model, x, cov_h, cov_f
    )

    assert len(model.constraints) > 0

    assert any(
        name.startswith("crew_size_")
        for name in model.constraints
    )

    assert any(
        name.startswith("minimum_gap_")
        for name in model.constraints
    )

    assert any(
        name.startswith("over_limit_")
        for name in model.constraints
    )

    assert any(
        name.startswith("holiday_coverage_")
        for name in model.constraints
    )


# ==================================================
# 3. ΕΚΤΕΛΕΣΗ ΕΝΟΣ ΣΤΑΔΙΟΥ ΒΕΛΤΙΣΤΟΠΟΙΗΣΗΣ
# ==================================================

def test_run_stage_returns_optimal_result(milp_data):

    model = pulp.LpProblem(
        "Test_MILP_Stage",
        pulp.LpMinimize
    )

    x = pulp.LpVariable(
        "test_variable",
        lowBound=0,
        upBound=10,
        cat=pulp.LpInteger
    )

    value, status = run_stage(
        model,
        "Test Stage",
        x
    )

    assert value == 0
    assert status == "Optimal"

    assert pulp.value(x) == 0

    # Ελέγχουμε ότι κλειδώθηκε η βέλτιστη τιμή.
    assert len(model.constraints) == 1


# ==================================================
# 4. ΣΥΝΟΛΙΚΗ ΕΚΤΕΛΕΣΗ MILP
# ==================================================

def test_milp_returns_schedule(milp_result):

    sched, results = milp_result

    assert len(sched) == config.DAYS
    assert len(results) == 7


def test_milp_schedule_has_no_rule_violations(milp_result):

    sched, results = milp_result

    errors = rules_errors(sched)

    assert errors == []


def test_milp_all_stages_are_optimal(milp_result):

    sched, results = milp_result

    assert len(results) == 7

    for title, value, status in results:

        assert status == "Optimal"


def test_milp_results_have_valid_structure(milp_result):

    sched, results = milp_result

    for result in results:

        assert isinstance(result, tuple)
        assert len(result) == 3

        title, value, status = result

        assert isinstance(title, str)
        assert isinstance(value, int)
        assert status == "Optimal"


# ==================================================
# 5. ΕΛΕΓΧΟΣ ΔΟΜΗΣ ΠΡΟΓΡΑΜΜΑΤΟΣ
# ==================================================

def test_milp_schedule_has_correct_crew_size(milp_result):

    sched, results = milp_result

    for day in sched:

        assert len(day["crew"]) == config.CREW


def test_milp_roles_belong_to_crew(milp_result):

    sched, results = milp_result

    for day in sched:

        assert day["duty"] in day["crew"]
        assert day["mech"] in day["crew"]
        assert day["elec"] in day["crew"]


def test_milp_roles_are_distinct(milp_result):

    sched, results = milp_result

    for day in sched:

        assert day["mech"] != day["elec"]
