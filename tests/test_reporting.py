
from core import reporting


# Αρχικοποίηση dummy δεδομένων για κάθε test.
def setup_dummy_data():
    from core import data

    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    return data


def test_totals_calculates_total_shifts():
    data = setup_dummy_data()

    summary = {
        member: {
            "shifts": [5, 4, 6][i] if i < 3 else 0,
            "over": 0,
            "hol": 0,
            "fri": 0
        }
        for i, member in enumerate(data.names)
    }

    result = reporting.totals(summary)

    assert result["σύνολο βαρδιών"] == 15


def test_totals_calculates_total_over():
    data = setup_dummy_data()

    summary = {
        member: {
            "shifts": 5,
            "over": [1, 0, 2][i] if i < 3 else 0,
            "hol": 0,
            "fri": 0
        }
        for i, member in enumerate(data.names)
    }

    result = reporting.totals(summary)

    assert result["συνολική υπέρβαση"] == 3


def test_totals_calculates_role_pool_over():
    data = setup_dummy_data()

    summary = {
        member: {
            "shifts": 5,
            "over": 2,
            "hol": 1,
            "fri": 1
        }
        for member in data.names
    }

    result = reporting.totals(summary)

    expected = sum(
        summary[member]["over"]
        for member in data.POOL
    )

    assert result["υπέρβαση ομάδας ρόλων"] == expected


def test_totals_calculates_members_with_holiday():
    data = setup_dummy_data()

    summary = {
        member: {
            "shifts": 5,
            "over": 1,
            "hol": 1 if i < 2 else 0,
            "fri": 0
        }
        for i, member in enumerate(data.names)
    }

    result = reporting.totals(summary)

    assert result["άτομα με αργία"] == 2


def test_totals_calculates_members_with_friday():
    data = setup_dummy_data()

    summary = {
        member: {
            "shifts": 5,
            "over": 1,
            "hol": 0,
            "fri": 1 if i < 3 else 0
        }
        for i, member in enumerate(data.names)
    }

    result = reporting.totals(summary)

    assert result["άτομα με Παρασκευή"] == 3


def test_print_measure_differences_counts_different_members(capsys):
    data = setup_dummy_data()

    names = data.names[:3]

    summaries = {
        "GA": {
            member: {"shifts": 5, "over": 0, "hol": 1, "fri": 1}
            for member in names
        },
        "SA": {
            member: {"shifts": 5, "over": 0, "hol": 1, "fri": 1}
            for member in names
        }
    }

    # Το δεύτερο μέλος έχει διαφορετικό αριθμό βαρδιών στο SA.
    summaries["SA"][names[1]]["shifts"] = 6

    total = reporting.print_measure_differences(
        summaries, names
    )

    output = capsys.readouterr().out

    assert total == 1
    assert "1 άτομα με διαφορά" in output


def test_print_measure_differences_counts_multiple_measures(capsys):
    data = setup_dummy_data()

    names = data.names[:2]

    summaries = {
        "GA": {
            member: {"shifts": 5, "over": 0, "hol": 1, "fri": 1}
            for member in names
        },
        "SA": {
            member: {"shifts": 5, "over": 0, "hol": 1, "fri": 1}
            for member in names
        }
    }

    # Το ίδιο μέλος έχει δύο διαφορετικά μέτρα.
    summaries["SA"][names[0]]["shifts"] = 6
    summaries["SA"][names[0]]["hol"] = 2

    total = reporting.print_measure_differences(
        summaries, names
    )

    capsys.readouterr()

    assert total == 2


def test_print_role_differences_counts_different_roles(capsys):
    data = setup_dummy_data()

    names = data.names[:2]

    summaries = {
        "GA": {
            member: {"duty": 1, "mech": 2, "elec": 3}
            for member in names
        },
        "SA": {
            member: {"duty": 1, "mech": 2, "elec": 3}
            for member in names
        }
    }

    # Αλλάζουμε δύο ρόλους για το ίδιο μέλος.
    summaries["SA"][names[0]]["duty"] = 4
    summaries["SA"][names[0]]["elec"] = 5

    total = reporting.print_role_differences(
        summaries, names
    )

    output = capsys.readouterr().out

    assert total == 2
    assert "ΡΟΛΟΙ" in output


def test_print_role_differences_returns_zero_when_identical(capsys):
    data = setup_dummy_data()

    names = data.names[:3]

    summaries = {
        "GA": {
            member: {"duty": 1, "mech": 2, "elec": 3}
            for member in names
        },
        "SA": {
            member: {"duty": 1, "mech": 2, "elec": 3}
            for member in names
        }
    }

    total = reporting.print_role_differences(
        summaries, names
    )

    output = capsys.readouterr().out

    assert total == 0
    assert "Καμία διαφορά." in output

def test_compare_handles_empty_results(capsys):
    reporting.compare({})

    output = capsys.readouterr().out

    assert "Δεν υπάρχουν διαθέσιμες λύσεις για σύγκριση." in output


def test_compare_ignores_results_without_schedule(capsys):
    reporting.compare({
        "GA": {
            "schedule": None,
            "time": 0.5
        }
    })

    output = capsys.readouterr().out

    assert "Δεν υπάρχουν διαθέσιμες λύσεις για σύγκριση." in output


def test_compare_recognizes_valid_schedule(monkeypatch, capsys):
    data = setup_dummy_data()

    # Δημιουργούμε ένα εικονικό πρόγραμμα 31 ημερών.
    schedule = [
        {
            "crew": [],
            "duty": "",
            "mech": "",
            "elec": ""
        }
        for _ in range(31)
    ]

    # Αντικαθιστούμε τους ελέγχους με ελεγχόμενες επιστροφές.
    monkeypatch.setattr(
        reporting,
        "rules_errors",
        lambda sched: []
    )

    monkeypatch.setattr(
        reporting,
        "summarize",
        lambda sched: {
            member: {
                "shifts": 0,
                "over": 0,
                "hol": 0,
                "fri": 0,
                "duty": 0,
                "mech": 0,
                "elec": 0
            }
            for member in data.names
        }
    )

    monkeypatch.setattr(
        reporting,
        "score",
        lambda sched: (0, 0, 0, 0, 0, 0, 0, 0)
    )

    reporting.compare({
        "GA": {
            "schedule": schedule,
            "time": 0.5,
            "stages": []
        }
    })

    output = capsys.readouterr().out

    assert "Όλοι οι σκληροί κανόνες ικανοποιούνται" in output
    assert "Έγκυρες λύσεις: 1 από 1" in output


def test_compare_recognizes_invalid_schedule(monkeypatch, capsys):
    data = setup_dummy_data()

    schedule = [{} for _ in range(31)]

    monkeypatch.setattr(
        reporting,
        "rules_errors",
        lambda sched: ["Εικονική παράβαση κανόνα"]
    )

    monkeypatch.setattr(
        reporting,
        "summarize",
        lambda sched: {
            member: {
                "shifts": 0,
                "over": 0,
                "hol": 0,
                "fri": 0,
                "duty": 0,
                "mech": 0,
                "elec": 0
            }
            for member in data.names
        }
    )

    monkeypatch.setattr(
        reporting,
        "score",
        lambda sched: (1, 0, 0, 0, 0, 0, 0, 0)
    )

    reporting.compare({
        "GA": {
            "schedule": schedule,
            "time": 0.5,
            "stages": []
        }
    })

    output = capsys.readouterr().out

    assert "1 παραβάσεις" in output
    assert "Έγκυρες λύσεις: 0 από 1" in output
    assert "Εικονική παράβαση κανόνα" in output


def test_compare_recognizes_optimal_cpsat_solution(monkeypatch, capsys):
    data = setup_dummy_data()

    monkeypatch.setattr(
        reporting,
        "rules_errors",
        lambda sched: []
    )

    monkeypatch.setattr(
        reporting,
        "summarize",
        lambda sched: {
            member: {
                "shifts": 0,
                "over": 0,
                "hol": 0,
                "fri": 0,
                "duty": 0,
                "mech": 0,
                "elec": 0
            }
            for member in data.names
        }
    )

    monkeypatch.setattr(
        reporting,
        "score",
        lambda sched: (0, 0, 0, 0, 0, 0, 0, 0)
    )

    reporting.compare({
        "CP-SAT": {
            "schedule": [{} for _ in range(31)],
            "time": 0.5,
            "stages": [
                ("Στάδιο 1", 0, "OPTIMAL"),
                ("Στάδιο 2", 10, "OPTIMAL")
            ]
        }
    })

    output = capsys.readouterr().out

    assert "CP-SAT: αποδείχθηκε βέλτιστο αποτέλεσμα" in output


def test_compare_displays_scores_for_all_algorithms(monkeypatch, capsys):
    data = setup_dummy_data()

    # Κάθε αλγόριθμος έχει διαφορετικό αναγνωριστικό στο πρόγραμμά του.
    results = {
        "GA": {"schedule": [{"algorithm": "GA"}], "time": 1.0},
        "SA": {"schedule": [{"algorithm": "SA"}], "time": 2.0},
        "CP-SAT": {"schedule": [{"algorithm": "CP-SAT"}], "time": 3.0},
        "MILP": {"schedule": [{"algorithm": "MILP"}], "time": 4.0},
    }

    # Εικονικά αποτελέσματα για να ελέγξουμε μόνο την παρουσίαση.
    monkeypatch.setattr(reporting, "rules_errors", lambda schedule: [])
    monkeypatch.setattr(
        reporting,
        "summarize",
        lambda schedule: {
            name: {"shifts": 0, "over": 0, "hol": 0, "fri": 0,
                   "duty": 0, "mech": 0, "elec": 0}
            for name in data.names
        }
    )

    scores = {
        "GA": (1, 2, 3, 4, 5, 6, 7, 8),
        "SA": (2, 3, 4, 5, 6, 7, 8, 9),
        "CP-SAT": (3, 4, 5, 6, 7, 8, 9, 10),
        "MILP": (4, 5, 6, 7, 8, 9, 10, 11),
    }

    monkeypatch.setattr(
        reporting,
        "score",
        lambda schedule: scores[schedule[0]["algorithm"]]
    )

    reporting.compare(results)

    output = capsys.readouterr().out

    # Ελέγχουμε ότι εμφανίζονται και οι τέσσερις βαθμολογίες.
    for algorithm, expected_score in scores.items():
        assert algorithm in output
        assert str(expected_score) in output