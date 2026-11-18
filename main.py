
import random
import time

from core import config
from core import data

from core.reporting import (
    print_setup,
    compare
)

from core.timing import print_timing_summary

from algorithms.genetic import evolve_ga
from algorithms.cpsat import solve_cpsat

from algorithms.simulated_annealing import solve_sa
from algorithms.milp import solve_milp
# ================= MAIN =================

def main():

    total_start = time.perf_counter()

    # Αναπαραγωγιμότητα τυχαίων επιλογών GA
    random.seed(config.SEED)

    # ---------- Φόρτωση δεδομένων ----------

    if config.DATA_SOURCE == "excel":

        m, mech, elec = data.load_excel(
            config.EXCEL_FILE,
            config.EXCEL_SHEET
        )

        print(
            f"Δεδομένα: {config.EXCEL_FILE} ({len(m)} άτομα)"
        )

    else:

        m, mech, elec = data.dummy_members()

        print("Δεδομένα: ψεύτικα (dummy)")

    # Αρχικοποίηση κοινών δεδομένων
    data.setup(m, mech, elec)

    print_setup()
    # ---------- Αποθήκευση αποτελεσμάτων αλγορίθμων ----------

    results = {}
    # ---------- Genetic Algorithm ----------


    print("\n=== GENETIC ALGORITHM ===", flush=True)

    ga_start = time.perf_counter()

    gs, gscore = evolve_ga()

    ga_time = time.perf_counter() - ga_start

    results["GA"] = {
        "schedule": gs,
        "score": gscore,
        "stages": [],
        "time": ga_time
    }

    print(
        f"\nΟ GA ολοκληρώθηκε σε {ga_time:.2f}s",
        flush=True
    )

    # ---------- Simulated Annealing ----------

    print("\n=== SIMULATED ANNEALING ===", flush=True)

    sa_start = time.perf_counter()

    sas, sascore = solve_sa(
        iterations_per_temp=100,
        max_levels=200,
        alpha=0.90,
        seed=config.SEED
    )

    sa_time = time.perf_counter() - sa_start

    results["SA"] = {
        "schedule": sas,
        "score": sascore,
        "stages": [],
        "time": sa_time
    }

    print(
        f"\nΟ SA ολοκληρώθηκε σε {sa_time:.2f}s",
        flush=True
    )

    # ---------- CP-SAT ----------

    print("\n=== CP-SAT ===", flush=True)

    cs = None
    cp_stages = []
    cp_time = 0.0

    try:

        cp_start = time.perf_counter()

        cs, cp_stages = solve_cpsat()

        cp_time = time.perf_counter() - cp_start

        results["CP-SAT"] = {
            "schedule": cs,
            "score": None,
            "stages": cp_stages,
            "time": cp_time
        }

        print(
            f"\nΤο CP-SAT ολοκληρώθηκε σε {cp_time:.2f}s",
            flush=True
        )

    except SystemExit as e:

        print(f"CP-SAT: {e}")

    # ---------- MILP ----------

    print("\n=== MILP ===", flush=True)

    ms = None
    milp_stages = []
    milp_time = 0.0

    try:

        milp_start = time.perf_counter()

        ms, milp_stages = solve_milp()

        milp_time = time.perf_counter() - milp_start

        results["MILP"] = {
            "schedule": ms,
            "score": None,
            "stages": milp_stages,
            "time": milp_time
        }

        print(
            f"\nΤο MILP ολοκληρώθηκε σε {milp_time:.2f}s",
            flush=True
        )

    except SystemExit as e:

        print(f"MILP: {e}")

    # ---------- Σύγκριση αποτελεσμάτων ----------

    # ---------- Σύγκριση αποτελεσμάτων ----------

    compare(results)

    # ---------- Χρονομέτρηση ----------

    print_timing_summary()

    print(
        f"\nΣΥΝΟΛΙΚΟΣ ΧΡΟΝΟΣ: "
        f"{time.perf_counter() - total_start:.2f} δευτερόλεπτα"
    )


if __name__ == "__main__":
    main()
