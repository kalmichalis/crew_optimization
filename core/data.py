
from collections import defaultdict
from datetime import date

from core.config import (
    RANKS,
    RANK_BY_NAME,
    RANK_LABEL,
    EXPECTED,
    AK_RANK,
)


# ================= ΚΑΤΑΣΤΑΣΗ ΔΕΔΟΜΕΝΩΝ =================

members = {}
names = []
N = 0

MECH = set()
ELEC = set()
POOL = set()
DUTY_OK = set()
ORDER = {}


# ================= ΔΗΜΙΟΥΡΓΙΑ DUMMY ΔΕΔΟΜΕΝΩΝ =================


def dummy_members(size=25, seed=42):

    import random
    from datetime import date, timedelta

    if not isinstance(size, int) or isinstance(size, bool):
        raise ValueError("Το size πρέπει να είναι ακέραιος αριθμός.")

    if size < 25 or size % 25 != 0:
        raise ValueError(
            "Το μέγεθος πρέπει να είναι πολλαπλάσιο του 25 "
            "και τουλάχιστον 25."
        )

    fake_names = {
        "Ανθυπασπιστής": [
            "Ανθ. Γιάννης", "Ανθ. Νίκος", "Ανθ. Δημήτρης",
            "Ανθ. Κώστας", "Ανθ. Μάκης"
        ],
        "Αρχικελευστής": [
            "Αρχ. Πέτρος", "Αρχ. Στέλιος", "Αρχ. Θανάσης",
            "Αρχ. Βασίλης", "Αρχ. Λευτέρης"
        ],
        "Επικελευστής": [
            "Επ. Σάκης", "Επ. Τάσος", "Επ. Ηλίας",
            "Επ. Χρήστος", "Επ. Άρης"
        ],
        "Κελευστής": [
            "Κελ. Μιχάλης", "Κελ. Παναγιώτης", "Κελ. Αντώνης",
            "Κελ. Ευάγγελος", "Κελ. Ορέστης"
        ],
        "Δίοπος": [
            "Δίοπ. Φώτης", "Δίοπ. Σωτήρης", "Δίοπ. Ρένος",
            "Δίοπ. Θεόδωρος", "Δίοπ. Άκης"
        ],
    }

    original_mech = {
        "Ανθ. Γιάννης", "Ανθ. Νίκος",
        "Αρχ. Πέτρος", "Αρχ. Στέλιος",
        "Αρχ. Θανάσης", "Αρχ. Βασίλης"
    }

    original_elec = {
        "Ανθ. Δημήτρης", "Ανθ. Κώστας",
        "Αρχ. Πέτρος", "Αρχ. Στέλιος",
        "Αρχ. Θανάσης", "Αρχ. Βασίλης"
    }

    # Ακριβής διατήρηση του αρχικού dataset.
    if size == 25:

        members_ = {}

        for label, rank, count, _ in RANKS:
            for i, name in enumerate(fake_names[label][:count]):
                members_[name] = {
                    "rank": rank,
                    "promoted": date(2015 + rank, 1 + i, 1)
                }

        return members_, original_mech, original_elec

    rng = random.Random(seed)

    members_ = {}
    mech = set()
    elec = set()

    multiplier = size // 25

    for label, rank, count, _ in RANKS:

        rank_names = list(fake_names[label][:count])

        # Δημιουργία επιπλέον συνθετικών ονομάτων.
        for i in range(5, 5 * multiplier):
            name = f"{label} Μέλος {i + 1:03d}"
            rank_names.append(name)

        # Δημιουργία ημερομηνιών προαγωγής.
        for i, name in enumerate(rank_names):

            promoted = (
                date(2015 + rank, 1, 1)
                + timedelta(days=rng.randint(0, 1800))
            )

            members_[name] = {
                "rank": rank,
                "promoted": promoted
            }

        extra_names = rank_names[5:]

        # Οι ειδικότητες περιορίζονται στους βαθμούς 4 και 5.
        if rank == 5:

            mech.update({
                name for name in rank_names
                if name in original_mech
            })

            elec.update({
                name for name in rank_names
                if name in original_elec
            })

            # Στον βαθμό 5 οι δύο ειδικότητες
            # παραμένουν σε διαφορετικά άτομα.
            available = [
                name for name in extra_names
            ]

            count_per_skill = round(len(available) * 0.4)

            selected = rng.sample(
                available, count_per_skill * 2
            )

            mech.update(selected[:count_per_skill])
            elec.update(selected[count_per_skill:])

        elif rank == 4:

            # Στον βαθμό 4 τα ίδια άτομα έχουν
            # και τις δύο ειδικότητες.
            mech.update({
                name for name in rank_names
                if name in original_mech
            })

            elec.update({
                name for name in rank_names
                if name in original_elec
            })

            count_per_skill = round(len(extra_names) * 0.8)

            selected = rng.sample(
                extra_names, count_per_skill
            )

            mech.update(selected)
            elec.update(selected)

    return members_, mech, elec




# ================= ΦΟΡΤΩΣΗ EXCEL =================

def _is_yes(value):

    return str(value).strip().lower() in {
        "1", "1.0", "x", "χ", "ναι", "yes", "true"
    }


def load_excel(path, sheet=0):

    import pandas as pd

    df = pd.read_excel(path, sheet_name=sheet)

    required = [
        "Όνομα", "Βαθμός", "Ημ_προαγωγής",
        "Μηχανικός", "Ηλεκτρολόγος"
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Λείπουν στήλες στο Excel: {missing}"
        )

    members_, mech, elec = {}, set(), set()

    for _, row in df.iterrows():

        if pd.isna(row["Όνομα"]):
            continue

        name = str(row["Όνομα"]).strip()
        label = str(row["Βαθμός"]).strip()

        if label not in RANK_BY_NAME:
            raise ValueError(
                f"Άγνωστος βαθμός '{label}' για {name}. "
                f"Επιτρεπτά: {list(RANK_BY_NAME)}"
            )

        if name in members_:
            raise ValueError(
                f"Διπλό όνομα στο Excel: {name}"
            )

        if pd.isna(row["Ημ_προαγωγής"]):
            raise ValueError(
                f"Λείπει ημερομηνία προαγωγής για {name}"
            )

        promoted = pd.to_datetime(
            row["Ημ_προαγωγής"]
        ).date()

        members_[name] = {
            "rank": RANK_BY_NAME[label],
            "promoted": promoted
        }

        if _is_yes(row["Μηχανικός"]):
            mech.add(name)

        if _is_yes(row["Ηλεκτρολόγος"]):
            elec.add(name)

    return members_, mech, elec


# ================= ΔΗΜΙΟΥΡΓΙΑ ΠΡΟΤΥΠΟΥ EXCEL =================

def write_template(path="personnel_template.xlsx"):

    import pandas as pd

    m, mech, elec = dummy_members()

    rows = [{
        "Όνομα": name,
        "Βαθμός": RANK_LABEL[v["rank"]],
        "Ημ_προαγωγής": v["promoted"],
        "Μηχανικός": int(name in mech),
        "Ηλεκτρολόγος": int(name in elec),
    } for name, v in m.items()]

    pd.DataFrame(rows).to_excel(path, index=False)

    print(f"Γράφτηκε το πρότυπο: {path}")


# ================= ΕΛΕΓΧΟΣ ΔΕΔΟΜΕΝΩΝ =================


def validate(members_, mech_, elec_, expected_counts=None):

    errs = []
    counts = defaultdict(int)

    for v in members_.values():
        counts[v["rank"]] += 1

    # Αν δεν δοθεί κατανομή, χρησιμοποιείται
    # η αρχική κατανομή των 25 ατόμων.
    if expected_counts is None:
        expected_counts = EXPECTED

    for rank, want in expected_counts.items():

        if counts[rank] != want:
            errs.append(
                f"βαθμός {RANK_LABEL[rank]}: "
                f"{counts[rank]} άτομα, αναμένονταν {want}"
            )

    for n in mech_ | elec_:

        if n not in members_:
            errs.append(
                f"προσόν σε άτομο που δεν υπάρχει: {n}"
            )

    duty_count = sum(
        1 for v in members_.values()
        if v["rank"] >= AK_RANK
    )

    if duty_count == 0:
        errs.append("Δεν υπάρχει διαθέσιμος υπόλογος")

    if len(mech_) == 0:
        errs.append("Δεν υπάρχει διαθέσιμος μηχανικός")

    if len(elec_) == 0:
        errs.append("Δεν υπάρχει διαθέσιμος ηλεκτρολόγος")

    if errs:
        raise ValueError(
            "Σφάλματα δεδομένων:\n  " + "\n  ".join(errs)
        )


# ================= ΑΡΧΙΚΟΠΟΙΗΣΗ ΔΕΔΟΜΕΝΩΝ =================

def setup(members_, mech_, elec_, expected_counts=None):

    global members, names, N
    global MECH, ELEC, POOL, DUTY_OK, ORDER

    validate(
        members_,
        mech_,
        elec_,
        expected_counts=expected_counts
    )

    members = members_
    names = list(members)
    N = len(names)

    MECH = set(mech_)
    ELEC = set(elec_)
    POOL = MECH | ELEC

    DUTY_OK = {
        m for m in names
        if members[m]["rank"] >= AK_RANK
    }

    # 0 = νεότερος.
    # Πρώτα βαθμός και μετά ημερομηνία προαγωγής.
    ORDER = {
        m: i
        for i, m in enumerate(sorted(
            names,
            key=lambda m: (
                members[m]["rank"],
                -members[m]["promoted"].toordinal()
            )
        ))
    }

# ================= ΠΡΟΣΟΝΤΑ ΠΡΟΣΩΠΙΚΟΥ =================

def quals_txt(m):

    q = []

    if m in DUTY_OK:
        q.append("υπόλογος")

    if m in MECH:
        q.append("μηχανικός")

    if m in ELEC:
        q.append("ηλεκτρολόγος")

    return ", ".join(q) or "πλήρωμα"
