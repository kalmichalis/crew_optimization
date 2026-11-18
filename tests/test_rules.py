
from core import config
from core import data


def test_dummy_data_setup():
    """
    Ελέγχει αν τα dummy δεδομένα δημιουργούνται
    και αρχικοποιούνται σωστά.
    """

    members, mech, elec = data.dummy_members()

    data.setup(members, mech, elec)

    # Ελέγχουμε ότι δημιουργήθηκαν 25 άτομα.
    assert data.N == 25

    # Ελέγχουμε ότι υπάρχουν μηχανικοί και ηλεκτρολόγοι.
    assert len(data.MECH) > 0
    assert len(data.ELEC) > 0

    # Ελέγχουμε ότι υπάρχουν ακριβώς 5 άτομα ανά βαθμό.
    for _, rank, expected_count, _ in config.RANKS:

        actual_count = sum(
            1 for member in data.members.values()
            if member["rank"] == rank
        )

        assert actual_count == expected_count
