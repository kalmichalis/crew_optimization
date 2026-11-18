
import time

from ortools.sat.python import cp_model

from core import config
from core import data
from core.timing import record_time


# ================= CP-SAT =================

def solve_cpsat(seed=None):

    model = cp_model.CpModel()

    # ---------- Μεταβλητές απόφασης ----------

    x = {
        (m, d): model.NewBoolVar(f"x_{m}_{d}")
        for m in data.names
        for d in config.R
    }

    duty = {
        (m, d): model.NewBoolVar(f"u_{m}_{d}")
        for m in data.names
        for d in config.R
    }

    mech = {
        (m, d): model.NewBoolVar(f"me_{m}_{d}")
        for m in data.names
        for d in config.R
    }

    elec = {
        (m, d): model.NewBoolVar(f"el_{m}_{d}")
        for m in data.names
        for d in config.R
    }

    # ---------- Βασικοί περιορισμοί ----------

    for d in config.R:

        model.Add(
            sum(x[m, d] for m in data.names) == config.CREW
        )

        model.AddExactlyOne([
            duty[m, d] for m in data.DUTY_OK
        ])

        model.AddExactlyOne([
            mech[m, d] for m in data.MECH
        ])

        model.AddExactlyOne([
            elec[m, d] for m in data.ELEC
        ])

        for m in data.names:

            model.AddImplication(
                duty[m, d], x[m, d]
            )

            model.AddImplication(
                mech[m, d], x[m, d]
            )

            model.AddImplication(
                elec[m, d], x[m, d]
            )

            model.Add(
                mech[m, d] + elec[m, d] <= 1
            )

            if m not in data.DUTY_OK:
                model.Add(duty[m, d] == 0)

            if m not in data.MECH:
                model.Add(mech[m, d] == 0)

            if m not in data.ELEC:
                model.Add(elec[m, d] == 0)

    # ---------- Απόσταση βαρδιών ----------

    for m in data.names:

        for d in range(
            config.DAYS - config.MIN_GAP + 1
        ):

            model.Add(
                sum(
                    x[m, d + k]
                    for k in range(config.MIN_GAP)
                ) <= 1
            )

    # ---------- Υπερβάσεις ----------

    MAX_LEVEL = 10

    over = {}
    lv = {}

    for m in data.names:

        over[m] = model.NewIntVar(
            0, MAX_LEVEL, f"over_{m}"
        )

        model.Add(
            sum(x[m, d] for d in config.R)
            <= config.CAP[data.members[m]["rank"]] + over[m]
        )

        lv[m] = [
            model.NewBoolVar(f"lv_{m}_{k}")
            for k in range(1, MAX_LEVEL + 1)
        ]

        model.Add(
            over[m] == sum(lv[m])
        )

        for k in range(MAX_LEVEL - 1):

            model.AddImplication(
                lv[m][k + 1],
                lv[m][k]
            )

    # ---------- Κάλυψη αργιών και Παρασκευών ----------

    cov_h = {
        m: model.NewBoolVar(f"ch_{m}")
        for m in data.names
    }

    cov_f = {
        m: model.NewBoolVar(f"cf_{m}")
        for m in data.names
    }

    hol_count = {}
    fri_count = {}

    for m in data.names:

        hol_count[m] = sum(
            x[m, d] for d in config.HOLIDAYS
        )

        fri_count[m] = sum(
            x[m, d] for d in config.FRIDAYS
        )

        model.Add(
            hol_count[m] >= cov_h[m]
        )

        model.Add(
            fri_count[m] >= cov_f[m]
        )

    results = []

    # ---------- Βοηθητική συνάρτηση σταδίων ----------

    def run_stage(title, expr, minimize):

        stage_start = time.perf_counter()

        if minimize:
            model.Minimize(expr)
        else:
            model.Maximize(expr)

        solver = cp_model.CpSolver()

        solver.parameters.max_time_in_seconds = config.TIME_LIMIT
        solver.parameters.num_workers = 8
        solver.parameters.random_seed = (
            config.SEED if seed is None else seed
        )

        print(
            f"\nCP-SAT: ξεκινά {title}...",
            flush=True
        )

        status = solver.Solve(model)

        elapsed = time.perf_counter() - stage_start

        record_time(f"CP-SAT {title}", elapsed)

        status_name = solver.StatusName(status)

        print(
            f"CP-SAT: ολοκληρώθηκε σε {elapsed:.2f}s "
            f"| κατάσταση: {status_name}",
            flush=True
        )

        if status == cp_model.INFEASIBLE:
            raise SystemExit(
                f"{title}: το μοντέλο είναι infeasible."
            )

        if status == cp_model.MODEL_INVALID:
            raise SystemExit(
                f"{title}: το μοντέλο είναι invalid."
            )

        if status == cp_model.UNKNOWN:
            raise SystemExit(
                f"{title}: δεν βρέθηκε λύση εντός χρόνου."
            )

        # Για λεξικογραφική βελτιστοποίηση απαιτούμε OPTIMAL.
        if status != cp_model.OPTIMAL:

            raise SystemExit(
                f"{title}: βρέθηκε FEASIBLE λύση, "
                "αλλά δεν αποδείχθηκε η βέλτιστη τιμή. "
                "Αύξησε το TIME_LIMIT."
            )

        value = round(solver.ObjectiveValue())

        # Κλειδώνουμε τη βέλτιστη τιμή για τα επόμενα στάδια.
        model.Add(expr == value)

        results.append((
            title,
            value,
            status_name
        ))

        return solver

    # ---------- Λεξικογραφική βελτιστοποίηση ----------

    # 1. Ελάχιστη συνολική υπέρβαση.
    run_stage(
        "1. Ελάχιστη συνολική υπέρβαση",
        sum(over[m] for m in data.names),
        True
    )

    # 2. Καλύτερη κατανομή υπερβάσεων.
    run_stage(
        "2. Κατανομή υπερβάσεων",
        sum(
            lv[m][k - 1] * (
                k * 100 + data.ORDER[m]
            )
            for m in data.names
            for k in range(1, MAX_LEVEL + 1)
        ),
        True
    )

    # 3. Μέγιστος αριθμός διαφορετικών ατόμων με αργία.
    run_stage(
        "3. Μέγιστη κάλυψη διαφορετικών ατόμων με αργία",
        sum(cov_h[m] for m in data.names),
        False
    )

    # 4. Σε ισοβαθμία, προτεραιότητα στους νεότερους.
    run_stage(
        "4. Προτεραιότητα νεότερων στις αργίες",
        sum(
            cov_h[m] * (data.N - data.ORDER[m])
            for m in data.names
        ),
        False
    )

    # 5. Κατανομή επιπλέον αργιών.
    run_stage(
        "5. Φορτίο αργιών",
        sum(
            data.ORDER[m] * hol_count[m]
            for m in data.names
        ),
        True
    )

    # 6. Μέγιστος αριθμός διαφορετικών ατόμων με Παρασκευή.
    run_stage(
        "6. Μέγιστη κάλυψη διαφορετικών ατόμων με Παρασκευή",
        sum(cov_f[m] for m in data.names),
        False
    )

    # 7. Σε ισοβαθμία, προτεραιότητα στους νεότερους.
    solver = run_stage(
        "7. Προτεραιότητα νεότερων στις Παρασκευές",
        sum(
            cov_f[m] * (data.N - data.ORDER[m])
            for m in data.names
        ),
        False
    )

    # ---------- Ανάκτηση προγράμματος ----------

    sched = []

    for d in config.R:

        crew = [
            m for m in data.names
            if solver.Value(x[m, d])
        ]

        sched.append({
            "crew": crew,

            "duty": next(
                m for m in crew
                if solver.Value(duty[m, d])
            ),

            "mech": next(
                m for m in crew
                if solver.Value(mech[m, d])
            ),

            "elec": next(
                m for m in crew
                if solver.Value(elec[m, d])
            ),
        })

    return sched, results
