# Βιβλιοθήκη MILP
import pulp

# Ρυθμίσεις του project
from core import config
from core import data

import time

from core.timing import record_time


# Μέγιστος αριθμός υπερβάσεων ανά άτομο.
# Χρησιμοποιείται ως άνω όριο για τις ακέραιες μεταβλητές.
MAX_LEVEL = 10


def create_decision_variables(model):
    """
    Δημιουργεί τις μεταβλητές απόφασης του προβλήματος.

    x[m, d]     = 1 αν το άτομο m συμμετέχει στη βάρδια της ημέρας d.
    duty[m, d]  = 1 αν το άτομο m αναλαμβάνει τον υπόλογο.
    mech[m, d]  = 1 αν το άτομο m αναλαμβάνει τον μηχανικό.
    elec[m, d]  = 1 αν το άτομο m αναλαμβάνει τον ηλεκτρολόγο.

    over[m]     = αριθμός βαρδιών πάνω από το επιτρεπόμενο όριο.
    lv[m, k]    = 1 αν το άτομο m έχει τουλάχιστον k υπερβάσεις.

    cov_h[m]    = 1 αν το άτομο m έχει τουλάχιστον μία αργία.
    cov_f[m]    = 1 αν το άτομο m έχει τουλάχιστον μία Παρασκευή.
    """

    # ---------- Μεταβλητές συμμετοχής στις βάρδιες ----------

    x = pulp.LpVariable.dicts(
        "x",
        [(m, d) for m in data.names for d in config.R],
        cat=pulp.LpBinary
    )

    # ---------- Μεταβλητές ανάθεσης ειδικών καθηκόντων ----------

    duty = pulp.LpVariable.dicts(
        "duty",
        [(m, d) for m in data.names for d in config.R],
        cat=pulp.LpBinary
    )

    mech = pulp.LpVariable.dicts(
        "mech",
        [(m, d) for m in data.names for d in config.R],
        cat=pulp.LpBinary
    )

    elec = pulp.LpVariable.dicts(
        "elec",
        [(m, d) for m in data.names for d in config.R],
        cat=pulp.LpBinary
    )

    # ---------- Μεταβλητές υπερβάσεων ----------

    over = pulp.LpVariable.dicts(
        "over",
        data.names,
        lowBound=0,
        upBound=MAX_LEVEL,
        cat=pulp.LpInteger
    )

    # Κάθε lv[m, k] δηλώνει αν υπάρχει τουλάχιστον k υπέρβαση.
    lv = pulp.LpVariable.dicts(
        "lv",
        [
            (m, k)
            for m in data.names
            for k in range(1, MAX_LEVEL + 1)
        ],
        cat=pulp.LpBinary
    )

    # ---------- Μεταβλητές κάλυψης αργιών και Παρασκευών ----------

    cov_h = pulp.LpVariable.dicts(
        "cov_h",
        data.names,
        cat=pulp.LpBinary
    )

    cov_f = pulp.LpVariable.dicts(
        "cov_f",
        data.names,
        cat=pulp.LpBinary
    )

    return x, duty, mech, elec, over, lv, cov_h, cov_f


def add_basic_constraints(model, x, duty, mech, elec):

    for d in config.R:

        # Ακριβώς CREW άτομα σε κάθε βάρδια.
        model += (
            pulp.lpSum(x[m, d] for m in data.names)
            == config.CREW,
            f"crew_size_{d}"
        )

        # Ακριβώς ένας επιλέξιμος υπόλογος.
        model += (
            pulp.lpSum(duty[m, d] for m in data.DUTY_OK)
            == 1,
            f"one_duty_{d}"
        )

        # Ακριβώς ένας επιλέξιμος μηχανικός.
        model += (
            pulp.lpSum(mech[m, d] for m in data.MECH)
            == 1,
            f"one_mech_{d}"
        )

        # Ακριβώς ένας επιλέξιμος ηλεκτρολόγος.
        model += (
            pulp.lpSum(elec[m, d] for m in data.ELEC)
            == 1,
            f"one_elec_{d}"
        )

        for m in data.names:

            # Τα ειδικά καθήκοντα ανατίθενται
            # μόνο σε άτομα που συμμετέχουν στη βάρδια.
            model += duty[m, d] <= x[m, d]
            model += mech[m, d] <= x[m, d]
            model += elec[m, d] <= x[m, d]

            # Μηχανικός και ηλεκτρολόγος διαφορετικά άτομα.
            model += mech[m, d] + elec[m, d] <= 1

            # Αποκλεισμός μη επιλέξιμων ατόμων.
            if m not in data.DUTY_OK:
                model += duty[m, d] == 0

            if m not in data.MECH:
                model += mech[m, d] == 0

            if m not in data.ELEC:
                model += elec[m, d] == 0


def add_gap_constraints(model, x):
    """
    Εξασφαλίζει την ελάχιστη απόσταση μεταξύ των βαρδιών.

    Για κάθε άτομο και κάθε συνεχόμενο παράθυρο
    MIN_GAP ημερών, επιτρέπεται το πολύ μία συμμετοχή.

    Παράδειγμα με MIN_GAP = 3:
    x[m, d] + x[m, d+1] + x[m, d+2] <= 1
    """

    for m in data.names:

        for d in range(config.DAYS - config.MIN_GAP + 1):

            model += (
                pulp.lpSum(
                    x[m, d + k]
                    for k in range(config.MIN_GAP)
                ) <= 1,
                f"minimum_gap_{m}_{d}"
            )


def add_over_constraints(model, x, over, lv):
    """
    Υπολογίζει τις υπερβάσεις βαρδιών ανά άτομο.

    over[m] = συνολικός αριθμός βαρδιών πάνω από το όριο.

    lv[m, k] = 1 όταν το άτομο m έχει τουλάχιστον k υπερβάσεις.

    Η δεύτερη μεταβλητή χρησιμοποιείται στο επόμενο
    στάδιο για τη δίκαιη κατανομή των υπερβάσεων.
    """

    for m in data.names:

        # Συνολικές βάρδιες του ατόμου.
        total_shifts = pulp.lpSum(
            x[m, d] for d in config.R
        )

        # Οι βάρδιες δεν μπορούν να ξεπερνούν
        # το κανονικό όριο συν τις υπερβάσεις.
        model += (
            total_shifts
            <= config.CAP[data.members[m]["rank"]] + over[m],
            f"over_limit_{m}"
        )

        # Ο αριθμός υπερβάσεων ισούται με το
        # πλήθος των ενεργών επιπέδων υπέρβασης.
        model += (
            over[m]
            == pulp.lpSum(
                lv[m, k]
                for k in range(1, MAX_LEVEL + 1)
            ),
            f"over_levels_{m}"
        )

        # Αν ενεργοποιηθεί ένα επίπεδο υπέρβασης,
        # πρέπει να έχουν ενεργοποιηθεί και όλα τα προηγούμενα.
        for k in range(1, MAX_LEVEL):

            model += (
                lv[m, k + 1] <= lv[m, k],
                f"ordered_levels_{m}_{k}"
            )


def add_coverage_constraints(model, x, cov_h, cov_f):
    """
    Δημιουργεί περιορισμούς για την κάλυψη αργιών και Παρασκευών.

    cov_h[m] = 1 αν το άτομο m έχει τουλάχιστον μία αργία.
    cov_f[m] = 1 αν το άτομο m έχει τουλάχιστον μία Παρασκευή.
    """

    for m in data.names:

        # Πλήθος αργιών που έχει αναλάβει το άτομο.
        holiday_count = pulp.lpSum(
            x[m, d] for d in config.HOLIDAYS
        )

        # Πλήθος Παρασκευών που έχει αναλάβει το άτομο.
        friday_count = pulp.lpSum(
            x[m, d] for d in config.FRIDAYS
        )

        # Αν έχει αργία, η μεταβλητή κάλυψης πρέπει να είναι 1.
        model += (
            holiday_count >= cov_h[m],
            f"holiday_coverage_{m}"
        )

        # Αν έχει Παρασκευή, η μεταβλητή κάλυψης πρέπει να είναι 1.
        model += (
            friday_count >= cov_f[m],
            f"friday_coverage_{m}"
        )


def run_stage(model, title, expression, minimize=True, seed=None):
    """
    Εκτελεί ένα στάδιο λεξικογραφικής βελτιστοποίησης.

    1. Ορίζει την αντικειμενική συνάρτηση.
    2. Εκτελεί τον solver CBC.
    3. Ελέγχει την πραγματική κατάσταση επίλυσης.
    4. Αποθηκεύει τη βέλτιστη τιμή ως περιορισμό,
       ώστε να διατηρηθεί στα επόμενα στάδια.

    Επιστρέφει (τιμή, κατάσταση) όπου η κατάσταση
    είναι το πραγματικό κείμενο που επέστρεψε ο solver.
    """

    start_time = time.perf_counter()

    # Ορισμός αντικειμενικής συνάρτησης.
    if minimize:
        model.sense = pulp.LpMinimize
    else:
        model.sense = pulp.LpMaximize

    model.setObjective(expression)

    # Δημιουργία και εκτέλεση του CBC solver.
    solver = pulp.PULP_CBC_CMD(
        msg=False,
        timeLimit=config.TIME_LIMIT,
        threads=8,
        options=[f"randomSeed {config.SEED if seed is None else seed}"]
    )

    print(f"\nMILP: ξεκινά {title}...", flush=True)

    status = model.solve(solver)

    elapsed = time.perf_counter() - start_time

    record_time(f"MILP {title}", elapsed)

    # Η πραγματική κατάσταση του solver και της λύσης.
    status_name = pulp.LpStatus[status]
    solution_status = pulp.LpSolution[model.sol_status]

    print(
        f"MILP: ολοκληρώθηκε σε {elapsed:.2f}s "
        f"| κατάσταση: {status_name} ({solution_status})",
        flush=True
    )

    # Αποδεχόμαστε μόνο αποδεδειγμένα βέλτιστη λύση.
    if (
        status != pulp.LpStatusOptimal
        or model.sol_status != pulp.LpSolutionOptimal
    ):
        raise SystemExit(
            f"{title}: δεν αποδείχθηκε βέλτιστη λύση "
            f"(κατάσταση: {status_name}, λύση: {solution_status})."
        )

    # Ανάκτηση βέλτιστης τιμής.
    value = round(pulp.value(expression))

    # Κλείδωμα της βέλτιστης τιμής για τα επόμενα στάδια.
    model += (
        expression == value,
        f"lock_stage_{len(model.constraints)}"
    )

    return value, status_name


def optimize_milp(
    model,
    over,
    lv,
    cov_h,
    cov_f,
    x,
    seed=None
):
    """
    Εκτελεί τα επτά στάδια λεξικογραφικής βελτιστοποίησης.

    Κάθε στάδιο κλειδώνει τη βέλτιστη τιμή του,
    πριν ξεκινήσει το επόμενο.
    """

    results = []

    # ---------- 1. Ελάχιστη συνολική υπέρβαση ----------

    value, status = run_stage(
        model,
        "1. Ελάχιστη συνολική υπέρβαση",
        pulp.lpSum(over[m] for m in data.names),
        minimize=True,
        seed=seed
    )

    results.append(("1. Ελάχιστη συνολική υπέρβαση", value, status))

    # ---------- 2. Καλύτερη κατανομή υπερβάσεων ----------

    value, status = run_stage(
        model,
        "2. Κατανομή υπερβάσεων",
        pulp.lpSum(
            lv[m, k] * (
                k * 100 + data.ORDER[m]
            )
            for m in data.names
            for k in range(1, MAX_LEVEL + 1)
        ),
        minimize=True,
        seed=seed
    )

    results.append(("2. Κατανομή υπερβάσεων", value, status))

    # ---------- 3. Μέγιστη κάλυψη διαφορετικών ατόμων με αργία ----------

    value, status = run_stage(
        model,
        "3. Μέγιστη κάλυψη αργιών",
        pulp.lpSum(cov_h[m] for m in data.names),
        minimize=False,
        seed=seed
    )

    results.append(("3. Μέγιστη κάλυψη αργιών", value, status))

    # ---------- 4. Προτεραιότητα νεότερων στις αργίες ----------

    value, status = run_stage(
        model,
        "4. Προτεραιότητα νεότερων στις αργίες",
        pulp.lpSum(
            cov_h[m] * (data.N - data.ORDER[m])
            for m in data.names
        ),
        minimize=False,
        seed=seed
    )

    results.append(("4. Προτεραιότητα νεότερων στις αργίες", value, status))

    # ---------- 5. Κατανομή επιπλέον αργιών ----------

    value, status = run_stage(
        model,
        "5. Φορτίο αργιών",
        pulp.lpSum(
            data.ORDER[m] * x[m, d]
            for m in data.names
            for d in config.HOLIDAYS
        ),
        minimize=True,
        seed=seed
    )

    results.append(("5. Φορτίο αργιών", value, status))

    # ---------- 6. Μέγιστη κάλυψη διαφορετικών ατόμων με Παρασκευή ----------

    value, status = run_stage(
        model,
        "6. Μέγιστη κάλυψη Παρασκευών",
        pulp.lpSum(cov_f[m] for m in data.names),
        minimize=False,
        seed=seed
    )

    results.append(("6. Μέγιστη κάλυψη Παρασκευών", value, status))

    # ---------- 7. Προτεραιότητα νεότερων στις Παρασκευές ----------

    value, status = run_stage(
        model,
        "7. Προτεραιότητα νεότερων στις Παρασκευές",
        pulp.lpSum(
            cov_f[m] * (data.N - data.ORDER[m])
            for m in data.names
        ),
        minimize=False,
        seed=seed
    )

    results.append(("7. Προτεραιότητα νεότερων στις Παρασκευές", value, status))

    return results


def solve_milp(seed=None):
    """
    Κεντρική συνάρτηση επίλυσης του προβλήματος με MILP.

    Δημιουργεί το μοντέλο, προσθέτει μεταβλητές και περιορισμούς,
    εκτελεί τα επτά στάδια βελτιστοποίησης και ανακτά το πρόγραμμα.
    """

    # ---------- Δημιουργία μοντέλου ----------

    model = pulp.LpProblem(
        "Crew_Scheduling_MILP",
        pulp.LpMinimize
    )

    # ---------- Δημιουργία μεταβλητών απόφασης ----------

    x, duty, mech, elec, over, lv, cov_h, cov_f = (
        create_decision_variables(model)
    )

    # ---------- Προσθήκη περιορισμών ----------

    add_basic_constraints(model, x, duty, mech, elec)

    add_gap_constraints(model, x)

    add_over_constraints(model, x, over, lv)

    add_coverage_constraints(model, x, cov_h, cov_f)

    # ---------- Εκτέλεση βελτιστοποίησης ----------

    results = optimize_milp(
        model,
        over,
        lv,
        cov_h,
        cov_f,
        x,
        seed=seed
    )

    # ---------- Ανάκτηση ημερήσιου προγράμματος ----------

    sched = []

    for d in config.R:

        # Τα άτομα που συμμετέχουν στη συγκεκριμένη βάρδια.
        crew = [
            m for m in data.names
            if pulp.value(x[m, d]) > 0.5
        ]

        # Δημιουργία εγγραφής με τη μορφή που χρησιμοποιεί
        # και ο υπόλοιπος κώδικας του project.
        sched.append({
            "crew": crew,

            "duty": next(
                m for m in crew
                if pulp.value(duty[m, d]) > 0.5
            ),

            "mech": next(
                m for m in crew
                if pulp.value(mech[m, d]) > 0.5
            ),

            "elec": next(
                m for m in crew
                if pulp.value(elec[m, d]) > 0.5
            ),
        })

    return sched, results