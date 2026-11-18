
import pytest

from core import data


def test_validate_accepts_correct_data():
    """
    Ελέγχει ότι η validate αποδέχεται
    τα σωστά dummy δεδομένα.
    """

    members, mech, elec = data.dummy_members()

    # Δεν πρέπει να προκύψει κανένα σφάλμα.
    data.validate(members, mech, elec)


def test_validate_rejects_wrong_rank_count():
    """
    Ελέγχει ότι η validate απορρίπτει
    δεδομένα με λανθασμένο αριθμό ατόμων ανά βαθμό.
    """

    members, mech, elec = data.dummy_members()

    # Αφαιρούμε ένα άτομο.
    removed_name = next(iter(members))
    del members[removed_name]

    # Αφαιρούμε και τυχόν προσόντα του,
    # ώστε να ελέγξουμε αποκλειστικά τον αριθμό ατόμων.
    mech.discard(removed_name)
    elec.discard(removed_name)

    with pytest.raises(ValueError):
        data.validate(members, mech, elec)


def test_validate_rejects_unknown_qualified_person():
    """
    Ελέγχει ότι απορρίπτεται ένα προσόν
    που αντιστοιχεί σε άτομο που δεν υπάρχει.
    """

    members, mech, elec = data.dummy_members()

    mech.add("ΑΝΥΠΑΡΚΤΟ ΑΤΟΜΟ")

    with pytest.raises(ValueError):
        data.validate(members, mech, elec)


def test_validate_rejects_missing_mechanic():
    """
    Ελέγχει ότι απορρίπτονται δεδομένα
    χωρίς διαθέσιμο μηχανικό.
    """

    members, mech, elec = data.dummy_members()

    with pytest.raises(ValueError):
        data.validate(members, set(), elec)


def test_validate_rejects_missing_electrician():
    """
    Ελέγχει ότι απορρίπτονται δεδομένα
    χωρίς διαθέσιμο ηλεκτρολόγο.
    """

    members, mech, elec = data.dummy_members()

    with pytest.raises(ValueError):
        data.validate(members, mech, set())


@pytest.mark.parametrize("size", [25, 50, 100, 200, 500])
def test_dummy_members_supports_different_sizes(size):
    """Ελέγχει τη δημιουργία διαφορετικών μεγεθών πληθυσμού."""

    members, mech, elec = data.dummy_members(size)

    assert len(members) == size

    expected_per_rank = size // 5

    for rank in data.EXPECTED:
        count = sum(
            1 for member in members.values()
            if member["rank"] == rank
        )
        assert count == expected_per_rank

    assert len(set(members)) == size

    assert mech.issubset(members)
    assert elec.issubset(members)


@pytest.mark.parametrize("size", [25, 50, 100, 200, 500])
def test_dummy_members_generated_data_is_valid(size):
    """Ελέγχει την επικύρωση των διαφορετικών πληθυσμών."""

    members, mech, elec = data.dummy_members(size)

    expected = {
        rank: size // 5
        for rank in data.EXPECTED
    }

    data.validate(
        members,
        mech,
        elec,
        expected_counts=expected
    )


def test_dummy_members_is_reproducible():
    """Ελέγχει ότι το ίδιο seed παράγει ίδια δεδομένα."""

    first = data.dummy_members(100, seed=42)
    second = data.dummy_members(100, seed=42)

    assert first == second


def test_dummy_members_rejects_invalid_size():
    """Ελέγχει ότι απορρίπτονται μη επιτρεπτά μεγέθη."""

    for size in [0, 10, 30, 70, -25, 25.5, True]:
        with pytest.raises(ValueError):
            data.dummy_members(size)


def test_dummy_members_preserves_qualification_rules():
    """Ελέγχει την κατανομή των ειδικοτήτων."""

    members, mech, elec = data.dummy_members(100)

    # Ειδικότητες μόνο στους βαθμούς 4 και 5.
    for name in mech | elec:
        assert members[name]["rank"] in {4, 5}

    # Στον βαθμό 5 δεν υπάρχει κοινό άτομο.
    senior_mech = {
        name for name in mech
        if members[name]["rank"] == 5
    }

    senior_elec = {
        name for name in elec
        if members[name]["rank"] == 5
    }

    assert senior_mech.isdisjoint(senior_elec)

    # Στον βαθμό 4 οι δύο ειδικότητες
    # αντιστοιχούν στα ίδια άτομα.
    rank4_mech = {
        name for name in mech
        if members[name]["rank"] == 4
    }

    rank4_elec = {
        name for name in elec
        if members[name]["rank"] == 4
    }

    assert rank4_mech == rank4_elec
