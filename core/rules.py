
from core import config
from core import data


# ================= ΕΛΕΓΧΟΙ ΚΑΝΟΝΩΝ =================

def rules_errors(sched):

    errs = []

    for d, day in enumerate(sched):

        # Έλεγχος αριθμού διαφορετικών ατόμων
        if len(set(day["crew"])) != config.CREW:
            errs.append(
                f"ημέρα {d+1}: "
                f"{len(set(day['crew']))} διακριτά άτομα"
            )

        # Έλεγχος υπόλογου
        if day["duty"] not in data.DUTY_OK:
            errs.append(
                f"ημέρα {d+1}: "
                f"υπόλογος {day['duty']} κάτω από αρχικελευστή"
            )

        # Έλεγχος μηχανικού
        if day["mech"] not in data.MECH:
            errs.append(
                f"ημέρα {d+1}: "
                f"μηχανικός {day['mech']} χωρίς προσόν"
            )

        # Έλεγχος ηλεκτρολόγου
        if day["elec"] not in data.ELEC:
            errs.append(
                f"ημέρα {d+1}: "
                f"ηλεκτρολόγος {day['elec']} χωρίς προσόν"
            )

        # Μηχανικός και ηλεκτρολόγος πρέπει να είναι διαφορετικοί
        if day["mech"] == day["elec"]:
            errs.append(
                f"ημέρα {d+1}: "
                "μηχανικός και ηλεκτρολόγος είναι το ίδιο άτομο"
            )

        # Όλοι οι υπεύθυνοι ρόλων πρέπει να ανήκουν στο πλήρωμα
        if not {
            day["duty"], day["mech"], day["elec"]
        } <= set(day["crew"]):

            errs.append(
                f"ημέρα {d+1}: ρόλος εκτός βάρδιας"
            )

    # Έλεγχος ελάχιστης απόστασης μεταξύ βαρδιών
    for m in data.names:

        ds = [
            d for d in config.R
            if m in sched[d]["crew"]
        ]

        for a, b in zip(ds, ds[1:]):

            if b - a < config.MIN_GAP:
                errs.append(
                    f"{m}: ημέρες {a+1} και {b+1} "
                    f"(απόσταση < {config.MIN_GAP})"
                )

    return errs


# ================= ΜΕΤΡΗΣΗ ΠΑΡΑΒΙΑΣΕΩΝ ΑΠΟΣΤΑΣΗΣ =================

def gap_conflict_count(sched):
    """Μετρά αποκλειστικά τις παραβιάσεις του MIN_GAP."""

    count = 0

    for m in data.names:

        ds = [
            d for d in config.R
            if m in sched[d]["crew"]
        ]

        for a, b in zip(ds, ds[1:]):

            if b - a < config.MIN_GAP:
                count += 1

    return count


# ================= ΣΤΑΤΙΣΤΙΚΑ ΠΡΟΣΩΠΙΚΟΥ =================

def summarize(sched):

    out = {}

    for m in data.names:

        ds = [
            d for d in config.R
            if m in sched[d]["crew"]
        ]

        out[m] = {
            "shifts": len(ds),

            "over": max(
                0,
                len(ds) - config.CAP[data.members[m]["rank"]]
            ),

            "hol": sum(
                d in config.HOLIDAYS for d in ds
            ),

            "fri": sum(
                d in config.FRIDAYS for d in ds
            ),

            "duty": sum(
                sched[d]["duty"] == m for d in config.R
            ),

            "mech": sum(
                sched[d]["mech"] == m for d in config.R
            ),

            "elec": sum(
                sched[d]["elec"] == m for d in config.R
            ),
        }

    return out
