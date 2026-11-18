from core import config
from core import data
from core.rules import rules_errors, summarize
from core.scoring import score


# ================= ΕΤΙΚΕΤΕΣ =================

# Ονόματα των 8 στοιχείων του tuple, με τη σειρά που τα επιστρέφει η score().
SCORE_LABELS = [
    "σκληρές παραβάσεις",
    "συνολική υπέρβαση",
    "κατανομή υπερβάσεων",
    "άτομα χωρίς αργία",
    "βάρος χωρίς αργία",
    "φορτίο αργιών",
    "άτομα χωρίς Παρασκευή",
    "βάρος χωρίς Παρασκευή",
]

# Μέτρα που βαθμολογούνται (μετράνε στη σύγκριση και στη βαθμολογία).
MEASURE_KEYS = ("shifts", "over", "hol", "fri")

# Ρόλοι: δεν ορίζονται από κανόνα, άρα δεν βελτιστοποιούνται.
ROLE_KEYS = ("duty", "mech", "elec")
ROLE_LABELS = {
    "duty": "υπόλογος",
    "mech": "μηχανικός",
    "elec": "ηλεκτρολόγος",
}


# ================= ΕΜΦΑΝΙΣΗ ΠΡΟΓΡΑΜΜΑΤΟΣ =================

def show(sched, title):

    print(
        f"\n{title} "
        "[Υ] υπόλογος, [Μ] μηχανικός, [Η] ηλεκτρολόγος"
    )

    for d, day in enumerate(sched):

        tag = (
            "αργία" if d in config.HOLIDAYS
            else "Παρ" if d in config.FRIDAYS
            else "καθημερινή"
        )

        parts = []

        for m in day["crew"]:

            roles = ""

            if day["duty"] == m:
                roles += " [Υ]"

            if day["mech"] == m:
                roles += " [Μ]"

            if day["elec"] == m:
                roles += " [Η]"

            parts.append(
                f"{m} ({data.quals_txt(m)}){roles}"
            )

        print(
            f"{d+1:2d} Δεκ ({tag}): "
            + ", ".join(parts)
        )


# ================= ΣΥΝΟΛΙΚΑ ΣΤΑΤΙΣΤΙΚΑ =================

def totals(s):

    return {
        "σύνολο βαρδιών": sum(
            v["shifts"] for v in s.values()
        ),

        "συνολική υπέρβαση": sum(
            v["over"] for v in s.values()
        ),

        "υπέρβαση ομάδας ρόλων": sum(
            s[m]["over"] for m in data.POOL
        ),

        "άτομα με αργία": sum(
            1 for m in data.names
            if s[m]["hol"] > 0
        ),

        "άτομα με Παρασκευή": sum(
            1 for m in data.names
            if s[m]["fri"] > 0
        ),
    }


# ================= ΒΑΘΜΟΛΟΓΙΑ =================

def print_score(name, s):

    print(f"{name}:")
    print(f"   Score (tuple): {s}")

    for label, value in zip(SCORE_LABELS, s):
        print(f"   {label:26s} {value}")


# ================= ΔΙΑΦΟΡΕΣ =================

def print_measure_differences(summaries, sorted_names):
    """Τυπώνει όλες τις διαφορές μέτρων, ομαδοποιημένες ανά μέτρο.
    Επιστρέφει το συνολικό πλήθος διαφορών."""

    total = 0

    print("\nΜΕΤΡΑ ΚΑΛΥΨΗΣ (βαθμολογούνται)")

    for key in MEASURE_KEYS:

        items = []

        for m in sorted_names:

            values = {
                name: summaries[name][m][key]
                for name in summaries
            }

            if len(set(values.values())) > 1:
                items.append((m, values))

        total += len(items)

        print(f"\n{config.REASONS[key]}: {len(items)} άτομα με διαφορά")

        if not items:
            print("   Καμία διαφορά.")

        for m, values in items:

            details = "  ".join(
                f"{name}={value}"
                for name, value in values.items()
            )

            print(f"   {m:22s} {details}")

    return total


def print_role_differences(summaries, sorted_names):
    """Τυπώνει όλες τις διαφορές ρόλων, ανά άτομο.
    Επιστρέφει το συνολικό πλήθος διαφορών (άτομο × ρόλος)."""

    total = 0
    lines = []

    for m in sorted_names:

        parts = []

        for key in ROLE_KEYS:

            values = {
                name: summaries[name][m][key]
                for name in summaries
            }

            if len(set(values.values())) > 1:

                total += 1

                details = "  ".join(
                    f"{name}={value}"
                    for name, value in values.items()
                )

                parts.append(f"{ROLE_LABELS[key]}: {details}")

        if parts:
            lines.append((m, parts))

    print("\nΡΟΛΟΙ (δεν ορίζονται από κανόνα, δεν βαθμολογούνται)")

    if not lines:
        print("   Καμία διαφορά.")

    for m, parts in lines:

        print(f"   {m:22s} " + " | ".join(parts))

    return total


# ================= ΣΥΓΚΡΙΣΗ ΑΛΓΟΡΙΘΜΩΝ =================

def compare(results):

    # Σειρά εμφάνισης των αλγορίθμων.
    algorithms = ["GA", "SA", "CP-SAT", "MILP"]

    # Κρατάμε μόνο τους αλγορίθμους που έχουν διαθέσιμη λύση.
    available = {
        name: results[name]
        for name in algorithms
        if name in results
        and results[name]["schedule"] is not None
    }

    if not available:
        print("\nΔεν υπάρχουν διαθέσιμες λύσεις για σύγκριση.")
        return

    # ---------- Έλεγχος κανόνων ----------

    print("\n================ ΕΛΕΓΧΟΣ ΚΑΝΟΝΩΝ ================")

    summaries = {}
    totals_by_algorithm = {}
    errors_by_algorithm = {}

    for name, result in available.items():

        sched = result["schedule"]

        errors = rules_errors(sched)
        errors_by_algorithm[name] = errors

        print(
            f"{name:8s}: "
            + (
                "Όλοι οι σκληροί κανόνες ικανοποιούνται"
                if not errors
                else f"{len(errors)} παραβάσεις"
            )
        )

        for error in errors[:10]:
            print("   ", error)

        summaries[name] = summarize(sched)
        totals_by_algorithm[name] = totals(summaries[name])

    # ---------- Συνοπτική σύγκριση ----------

    print("\n================ ΣΥΝΟΨΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ================")

    print(f"{'Μέτρο':35s}", end="")

    for name in available:
        print(f"{name:>12s}", end="")

    print()

    for metric in totals_by_algorithm[next(iter(available))]:

        print(f"{metric:35s}", end="")

        for name in available:

            value = totals_by_algorithm[name][metric]

            print(f"{value:12}", end="")

        print()

    # ---------- Χρόνοι εκτέλεσης ----------

    print("\n================ ΧΡΟΝΟΙ ΕΚΤΕΛΕΣΗΣ ================")

    for name, result in available.items():

        print(
            f"{name:8s}: {result['time']:.2f} δευτερόλεπτα"
        )

    # ---------- Διαφορές ----------

    sorted_names = sorted(data.names, key=data.ORDER.get)

    print("\n================ ΔΙΑΦΟΡΕΣ ΑΝΑ ΑΤΟΜΟ ================")

    measure_diffs = print_measure_differences(summaries, sorted_names)
    role_diffs = print_role_differences(summaries, sorted_names)

    if measure_diffs == 0 and role_diffs == 0:
        print("\nΌλοι οι αλγόριθμοι έχουν ίδια κατανομή.")
    else:
        print(
            f"\nΣύνολο διαφορών μέτρων: {measure_diffs} "
            f"(από {len(data.names) * len(MEASURE_KEYS)} μετρήσεις)"
        )
        print(
            f"Σύνολο διαφορών ρόλων: {role_diffs} "
            f"(από {len(data.names) * len(ROLE_KEYS)} μετρήσεις, "
            "δεν βαθμολογούνται)"
        )

    # ---------- Βαθμολογίες ----------

    print("\n================ ΒΑΘΜΟΛΟΓΙΕΣ ================")

    for name, result in available.items():

        print()

        print_score(name, score(result["schedule"]))

        # Οι ακριβείς solvers επιστρέφουν αποτελέσματα ανά στάδιο.
        stages = result.get("stages", [])

        if stages:
            print("   Στάδια:")

        for title, value, status in stages:

            print(
                f"     {title}: {value} ({status})"
            )

    # ---------- Συμπέρασμα ----------

    print("\n================ ΣΥΜΠΕΡΑΣΜΑ ================")

    valid_algorithms = [
        name
        for name in available
        if not errors_by_algorithm[name]
    ]

    print(
        f"Έγκυρες λύσεις: {len(valid_algorithms)} "
        f"από {len(available)}"
    )

    if valid_algorithms:

        print(
            "Αλγόριθμοι με έγκυρη λύση: "
            + ", ".join(valid_algorithms)
        )

    # Ελέγχουμε αν όλα τα στάδια των exact solvers είναι Optimal.
    for name in ("CP-SAT", "MILP"):

        if name not in available:
            continue

        stages = available[name].get("stages", [])

        if stages and all(
                str(status).upper() == "OPTIMAL"
                for _, _, status in stages
        ):

            print(
                f"{name}: αποδείχθηκε βέλτιστο αποτέλεσμα "
                "σε όλα τα στάδια."
            )

        elif stages:

            print(
                f"{name}: δεν αποδείχθηκε βέλτιστο αποτέλεσμα "
                "σε όλα τα στάδια."
            )

    # ---------- Προαιρετική εμφάνιση προγραμμάτων ----------

    if config.SHOW_SCHEDULES:

        for name, result in available.items():

            show(
                result["schedule"],
                f"{name} ΠΡΟΓΡΑΜΜΑ"
            )


# ================= ΠΛΗΡΟΦΟΡΙΕΣ ΠΡΟΒΛΗΜΑΤΟΣ =================

def print_setup():

    print("\n================ ΔΕΔΟΜΕΝΑ ΠΡΟΒΛΗΜΑΤΟΣ ================\n")

    print(f"Πηγή δεδομένων: {config.DATA_SOURCE}")
    print(f"Αριθμός ατόμων: {data.N}")
    print(f"Ημέρες προγραμματισμού: {config.DAYS}")
    print(f"Άτομα ανά βάρδια: {config.CREW}")

    print(f"\nΔιαθέσιμοι μηχανικοί: {len(data.MECH)}")
    print(f"Διαθέσιμοι ηλεκτρολόγοι: {len(data.ELEC)}")
    print(f"Διαθέσιμοι υπόλογοι: {len(data.DUTY_OK)}")

    print("\nORDER (νεότερος πρώτος):")

    for m in sorted(data.names, key=data.ORDER.get):

        print(
            f"  {data.ORDER[m]:2d} {m:22s} "
            f"βαθμός {data.members[m]['rank']}  "
            f"προαγωγή {data.members[m]['promoted']}"
        )

    # ---------- Ανάλυση αναγκαστικών υπερβάσεων ----------

    forced_pool = max(
        0,
        2 * config.DAYS - sum(
            config.CAP[data.members[m]["rank"]]
            for m in data.POOL
        )
    )

    total_over = max(
        0,
        config.DAYS * config.CREW - sum(
            config.CAP[data.members[m]["rank"]]
            for m in data.names
        )
    )

    print("\nΑΝΑΛΥΣΗ ΠΕΡΙΟΡΙΣΜΩΝ")

    print(
        f"  Αναγκαστικές υπερβάσεις ομάδας ρόλων: "
        f"{forced_pool}"
    )

    print(
        f"  Συνολικές αναγκαστικές υπερβάσεις: "
        f"{total_over}"
    )

    print(
        f"  Μέγιστες βάρδιες ανά άτομο "
        f"με απόσταση {config.MIN_GAP}: "
        f"{len(range(0, config.DAYS, config.MIN_GAP))}"
    )

    print(
        f"  Αργίες: {len(config.HOLIDAYS) * config.CREW} "
        f"θέσεις για {data.N} άτομα"
    )

    print(
        f"  Παρασκευές: {len(config.FRIDAYS) * config.CREW} "
        f"θέσεις για {data.N} άτομα\n"
    )