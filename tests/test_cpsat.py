
import pytest

from core import data, config
from algorithms.cpsat import solve_cpsat


@pytest.fixture(scope="module")
def cpsat_result():

    # Αρχικοποίηση δοκιμαστικών δεδομένων
    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    # Εκτέλεση του CP-SAT μία φορά
    sched, results = solve_cpsat()

    return sched, results


def test_cpsat_returns_schedule(cpsat_result):

    sched, results = cpsat_result

    assert len(sched) == config.DAYS
    assert len(results) == 7



from core import rules


def test_cpsat_schedule_has_no_rule_violations(cpsat_result):

    sched, results = cpsat_result

    errors = rules.rules_errors(sched)

    assert errors == []
