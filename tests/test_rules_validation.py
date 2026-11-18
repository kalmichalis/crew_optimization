
from core import config
from core import data
from core import rules




def create_valid_schedule():
    """
    Δημιουργεί έγκυρο πρόγραμμα 31 ημερών
    για τις δοκιμές των κανόνων.
    """

    members, mech, elec = data.dummy_members()
    data.setup(members, mech, elec)

    # Δημιουργούμε τρεις διαφορετικές ομάδες.
    # Κάθε ομάδα έχει 5 άτομα και τους τρεις ρόλους.
    teams = [
        {
            "crew": [
                "Ανθ. Μάκης",
                "Αρχ. Πέτρος",
                "Ανθ. Δημήτρης",
                "Δίοπ. Φώτης",
                "Δίοπ. Σωτήρης"
            ],
            "duty": "Ανθ. Μάκης",
            "mech": "Αρχ. Πέτρος",
            "elec": "Ανθ. Δημήτρης"
        },
        {
            "crew": [
                "Αρχ. Λευτέρης",
                "Αρχ. Στέλιος",
                "Ανθ. Κώστας",
                "Δίοπ. Ρένος",
                "Δίοπ. Θεόδωρος"
            ],
            "duty": "Αρχ. Λευτέρης",
            "mech": "Αρχ. Στέλιος",
            "elec": "Ανθ. Κώστας"
        },
        {
            "crew": [
                "Αρχ. Θανάσης",
                "Ανθ. Γιάννης",
                "Αρχ. Βασίλης",
                "Δίοπ. Άκης",
                "Κελ. Μιχάλης"
            ],
            "duty": "Αρχ. Θανάσης",
            "mech": "Ανθ. Γιάννης",
            "elec": "Αρχ. Βασίλης"
        }
    ]

    schedule = []

    # Εναλλάσσουμε τις τρεις ομάδες για 31 ημέρες.
    for day in config.R:

        team = teams[day % len(teams)]

        schedule.append({
            "crew": team["crew"].copy(),
            "duty": team["duty"],
            "mech": team["mech"],
            "elec": team["elec"]
        })

    return schedule


def test_valid_schedule_has_no_errors():

    schedule = create_valid_schedule()

    errors = rules.rules_errors(schedule)

    assert errors == []


def test_detects_wrong_crew_size():

    schedule = create_valid_schedule()

    # Αφαιρούμε ένα άτομο από το πλήρωμα.
    schedule[0]["crew"].pop()

    errors = rules.rules_errors(schedule)

    assert any("διακριτά άτομα" in error for error in errors)


def test_detects_invalid_duty():

    schedule = create_valid_schedule()

    schedule[0]["duty"] = "ΑΝΥΠΑΡΚΤΟ ΑΤΟΜΟ"

    errors = rules.rules_errors(schedule)

    assert any("υπόλογος" in error for error in errors)


def test_detects_invalid_mechanic():

    schedule = create_valid_schedule()

    schedule[0]["mech"] = "ΑΝΥΠΑΡΚΤΟ ΑΤΟΜΟ"

    errors = rules.rules_errors(schedule)

    assert any("μηχανικός" in error for error in errors)


def test_detects_invalid_electrician():

    schedule = create_valid_schedule()

    schedule[0]["elec"] = "ΑΝΥΠΑΡΚΤΟ ΑΤΟΜΟ"

    errors = rules.rules_errors(schedule)

    assert any("ηλεκτρολόγος" in error for error in errors)


def test_detects_same_mechanic_and_electrician():

    schedule = create_valid_schedule()

    schedule[0]["elec"] = schedule[0]["mech"]

    errors = rules.rules_errors(schedule)

    assert any("ίδιο άτομο" in error for error in errors)


def test_detects_role_outside_crew():

    schedule = create_valid_schedule()

    # Αλλάζουμε τον μηχανικό με άλλο έγκυρο μηχανικό,
    # που δεν συμμετέχει στο πλήρωμα.
    schedule[0]["mech"] = next(
        name for name in data.MECH
        if name not in schedule[0]["crew"]
    )

    errors = rules.rules_errors(schedule)

    assert any("ρόλος εκτός βάρδιας" in error for error in errors)



def test_gap_conflict_count_returns_zero():
    """
    Ελέγχει ότι ένα έγκυρο πρόγραμμα
    δεν έχει παραβιάσεις ελάχιστης απόστασης.
    """

    schedule = create_valid_schedule()

    conflicts = rules.gap_conflict_count(schedule)

    assert conflicts == 0


def test_gap_conflict_count_detects_conflicts():
    """
    Ελέγχει ότι εντοπίζονται οι παραβιάσεις
    όταν το ίδιο άτομο εμφανίζεται πολύ σύντομα ξανά.
    """

    schedule = create_valid_schedule()

    # Παίρνουμε ένα άτομο από την πρώτη ημέρα.
    member = schedule[0]["crew"][3]

    # Το τοποθετούμε και στην τρίτη ημέρα.
    schedule[2]["crew"][3] = member

    conflicts = rules.gap_conflict_count(schedule)

    # Το άτομο εμφανίζεται στις ημέρες 1, 3 και 4.
    # Επομένως υπάρχουν δύο παραβιάσεις.
    assert conflicts == 2



def test_summarize_returns_all_members():
    """
    Ελέγχει ότι η summarize επιστρέφει
    στατιστικά για όλα τα μέλη.
    """

    schedule = create_valid_schedule()

    summary = rules.summarize(schedule)

    assert len(summary) == data.N

    for member in data.names:
        assert member in summary


def test_summarize_contains_expected_fields():
    """
    Ελέγχει ότι κάθε μέλος έχει
    όλα τα αναμενόμενα στατιστικά πεδία.
    """

    schedule = create_valid_schedule()

    summary = rules.summarize(schedule)

    expected_fields = {
        "shifts",
        "over",
        "hol",
        "fri",
        "duty",
        "mech",
        "elec"
    }

    for stats in summary.values():
        assert set(stats.keys()) == expected_fields


def test_summarize_counts_roles_correctly():
    """
    Ελέγχει ότι οι αναθέσεις ρόλων
    υπολογίζονται σωστά.
    """

    schedule = create_valid_schedule()

    summary = rules.summarize(schedule)

    for member in data.names:

        assert summary[member]["duty"] == sum(
            day["duty"] == member for day in schedule
        )

        assert summary[member]["mech"] == sum(
            day["mech"] == member for day in schedule
        )

        assert summary[member]["elec"] == sum(
            day["elec"] == member for day in schedule
        )


def test_summarize_counts_total_shifts():
    """
    Ελέγχει ότι το άθροισμα των βαρδιών
    ισούται με τις ημέρες επί τα άτομα ανά βάρδια.
    """

    schedule = create_valid_schedule()

    summary = rules.summarize(schedule)

    total_shifts = sum(
        stats["shifts"] for stats in summary.values()
    )

    assert total_shifts == config.DAYS * config.CREW



from core import scoring


def test_score_returns_eight_criteria():
    """
    Ελέγχει ότι η score επιστρέφει
    και τα οκτώ κριτήρια αξιολόγησης.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)

    assert isinstance(result, tuple)
    assert len(result) == 8


def test_score_valid_schedule_has_zero_hard_violations():
    """
    Ελέγχει ότι ένα έγκυρο πρόγραμμα
    έχει μηδενικές παραβιάσεις κανόνων.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)

    assert result[0] == 0


def test_score_penalizes_invalid_schedule():
    """
    Ελέγχει ότι ένα πρόγραμμα με παραβίαση
    παίρνει μεγαλύτερη ποινή στο πρώτο κριτήριο.
    """

    schedule = create_valid_schedule()

    # Αφαιρούμε τον μηχανικό από το πλήρωμα.
    schedule[0]["crew"].remove(schedule[0]["mech"])

    result = scoring.score(schedule)

    assert result[0] > 0


def test_score_calculates_distribution_penalty():
    """
    Ελέγχει ότι η ποινή κατανομής υπερβάσεων
    υπολογίζεται σωστά για όλα τα μέλη.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected_dist = sum(
        k * 100 + data.ORDER[member]
        for member in data.names
        for k in range(1, summary[member]["over"] + 1)
    )

    assert result[2] == expected_dist


def test_score_counts_total_over_correctly():
    """
    Ελέγχει ότι η score υπολογίζει σωστά
    το άθροισμα των υπερβάσεων.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected_over = sum(
        stats["over"] for stats in summary.values()
    )

    assert result[1] == expected_over


def test_score_counts_members_without_holidays():
    """
    Ελέγχει πόσα μέλη δεν έχουν συμμετάσχει
    σε βάρδια αργίας.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected = sum(
        1 for member in data.names
        if summary[member]["hol"] == 0
    )

    assert result[3] == expected



def test_score_calculates_holiday_priority():
    """
    Ελέγχει την ποινή προτεραιότητας για τα μέλη
    που δεν έχουν συμμετάσχει σε βάρδια αργίας.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected = sum(
        data.N - data.ORDER[member]
        for member in data.names
        if summary[member]["hol"] == 0
    )

    assert result[4] == expected



def test_score_calculates_holiday_load():
    """
    Ελέγχει τον υπολογισμό του συνολικού φορτίου αργιών.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected = sum(
        data.ORDER[member] * summary[member]["hol"]
        for member in data.names
    )

    assert result[5] == expected



def test_score_counts_members_without_fridays():
    """
    Ελέγχει πόσα μέλη δεν έχουν συμμετάσχει
    σε βάρδια Παρασκευής.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected = sum(
        1 for member in data.names
        if summary[member]["fri"] == 0
    )

    assert result[6] == expected



def test_score_calculates_friday_priority():
    """
    Ελέγχει την ποινή προτεραιότητας για τα μέλη
    που δεν έχουν συμμετάσχει σε βάρδια Παρασκευής.
    """

    schedule = create_valid_schedule()

    result = scoring.score(schedule)
    summary = rules.summarize(schedule)

    expected = sum(
        data.N - data.ORDER[member]
        for member in data.names
        if summary[member]["fri"] == 0
    )

    assert result[7] == expected



def test_score_uses_lexicographic_order():
    """
    Ελέγχει ότι η σύγκριση των βαθμολογιών
    ακολουθεί λεξικογραφική σειρά.
    """

    better = (0, 5, 100, 10, 200, 300, 15, 400)
    worse = (1, 0, 0, 0, 0, 0, 0, 0)

    assert better < worse

def test_score_uses_next_criterion_when_previous_are_equal():
    """
    Ελέγχει ότι όταν δύο βαθμολογίες είναι ίδιες
    στα πρώτα κριτήρια, συγκρίνεται το επόμενο.
    """

    better = (0, 5, 10, 20, 30, 40, 50, 60)
    worse = (0, 6, 0, 0, 0, 0, 0, 0)

    assert better < worse

def test_score_compares_third_criterion():
    """
    Ελέγχει ότι η σύγκριση προχωρά στο τρίτο κριτήριο
    όταν τα δύο πρώτα είναι ίδια.
    """

    better = (0, 5, 10, 20, 30, 40, 50, 60)
    worse = (0, 5, 11, 0, 0, 0, 0, 0)

    assert better < worse