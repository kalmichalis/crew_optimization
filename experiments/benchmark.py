
import random
import time
import csv
import os
from core import config, data

from algorithms.genetic import evolve_ga
from algorithms.simulated_annealing import solve_sa
from algorithms.cpsat import solve_cpsat
from algorithms.milp import solve_milp

from core.rules import rules_errors
from core.scoring import score


# ================= ΡΥΘΜΙΣΕΙΣ BENCHMARK =================

POPULATION_SIZES = [25, 50]
DATASET_SEED = 42
SEEDS = [42, 123, 2026]
RESULTS_FILE = "benchmark_results.csv"


def initialize_dataset(size):
    """Δημιουργία και αρχικοποίηση κοινού dataset."""

    members, mech, elec = data.dummy_members(
        size=size,
        seed=DATASET_SEED
    )

    expected = {
        rank: size // 5
        for rank in data.EXPECTED
    }

    data.setup(
        members,
        mech,
        elec,
        expected_counts=expected
    )


def evaluate_result(schedule):
    """Έλεγχος εγκυρότητας και υπολογισμός κοινής βαθμολογίας."""

    if schedule is None:
        return None, None

    errors = rules_errors(schedule)
    result_score = score(schedule)

    return len(errors) == 0, result_score

def save_results(results):
    """Αποθήκευση αποτελεσμάτων benchmark σε CSV."""

    file_exists = os.path.isfile(RESULTS_FILE)

    with open(RESULTS_FILE, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "population",
                "seed",
                "algorithm",
                "time",
                "valid",
                "score",
                "status"
            ]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(results)

def run_genetic(seed):
    """Εκτέλεση και αξιολόγηση του Genetic Algorithm."""

    random.seed(seed)

    start = time.perf_counter()

    schedule, algorithm_score = evolve_ga()

    elapsed = time.perf_counter() - start

    valid, common_score = evaluate_result(schedule)

    print("\n=== GENETIC ALGORITHM ===")
    print(f"Χρόνος: {elapsed:.2f} sec")
    print(f"Έγκυρο πρόγραμμα: {valid}")
    print(f"Βαθμολογία αλγορίθμου: {algorithm_score}")
    print(f"Κοινή βαθμολογία: {common_score}")

    return {
        "algorithm": "GA",
        "time": elapsed,
        "valid": valid,
        "score": common_score,
        "status": "completed"
    }


def run_simulated_annealing(seed):
    """Εκτέλεση και αξιολόγηση του Simulated Annealing."""

    start = time.perf_counter()

    schedule, algorithm_score = solve_sa(
        iterations_per_temp=100,
        max_levels=200,
        alpha=0.90,
        seed=seed
    )

    elapsed = time.perf_counter() - start

    valid, common_score = evaluate_result(schedule)

    print("\n=== SIMULATED ANNEALING ===")
    print(f"Χρόνος: {elapsed:.2f} sec")
    print(f"Έγκυρο πρόγραμμα: {valid}")
    print(f"Βαθμολογία αλγορίθμου: {algorithm_score}")
    print(f"Κοινή βαθμολογία: {common_score}")

    return {
        "algorithm": "SA",
        "time": elapsed,
        "valid": valid,
        "score": common_score,
        "status": "completed"
    }


def run_cpsat(seed):
    """Εκτέλεση και αξιολόγηση του CP-SAT."""

    print("\n=== CP-SAT ===")

    start = time.perf_counter()

    try:
        schedule, stages = solve_cpsat(seed=seed)

        elapsed = time.perf_counter() - start

        valid, common_score = evaluate_result(schedule)

        print(f"Χρόνος: {elapsed:.2f} sec")
        print(f"Έγκυρο πρόγραμμα: {valid}")
        print(f"Κοινή βαθμολογία: {common_score}")
        print(f"Στάδια: {len(stages)}")

        return {
            "algorithm": "CP-SAT",
            "time": elapsed,
            "valid": valid,
            "score": common_score,
            "status": "completed"
        }

    except SystemExit as e:
        elapsed = time.perf_counter() - start

        print(f"CP-SAT δεν ολοκληρώθηκε: {e}")
        print(f"Χρόνος μέχρι τη διακοπή: {elapsed:.2f} sec")

        return {
            "algorithm": "CP-SAT",
            "time": elapsed,
            "valid": None,
            "score": None,
            "status": "failed"
        }

def run_milp(seed):
    """Εκτέλεση και αξιολόγηση του MILP."""

    print("\n=== MILP ===")

    start = time.perf_counter()

    try:
        schedule, stages = solve_milp(seed=seed)

        elapsed = time.perf_counter() - start

        valid, common_score = evaluate_result(schedule)

        print(f"Χρόνος: {elapsed:.2f} sec")
        print(f"Έγκυρο πρόγραμμα: {valid}")
        print(f"Κοινή βαθμολογία: {common_score}")
        print(f"Στάδια: {len(stages)}")

        return {
            "algorithm": "MILP",
            "time": elapsed,
            "valid": valid,
            "score": common_score,
            "status": "completed"
        }

    except SystemExit as e:
        elapsed = time.perf_counter() - start

        print(f"MILP δεν ολοκληρώθηκε: {e}")
        print(f"Χρόνος μέχρι τη διακοπή: {elapsed:.2f} sec")

        return {
            "algorithm": "MILP",
            "time": elapsed,
            "valid": None,
            "score": None,
            "status": "failed"
        }

def run_all_algorithms(population_size):
    """Εκτέλεση όλων των αλγορίθμων για συγκεκριμένο πληθυσμό."""

    print("\n" + "=" * 60)
    print(f"BENCHMARK ΓΙΑ {population_size} ΑΤΟΜΑ")
    print("=" * 60)

    initialize_dataset(population_size)

    print(f"Dataset: {data.N} άτομα")

    results = []

    for seed in SEEDS:
        print(f"\nΕΠΑΝΑΛΗΨΗ ΜΕ SEED: {seed}")

        for run_algorithm in [
            run_genetic,
            run_simulated_annealing,
            run_cpsat,
            run_milp
        ]:
            result = run_algorithm(seed)

            result["population"] = population_size
            result["seed"] = seed

            results.append(result)

    save_results(results)

    print(f"\nΤα αποτελέσματα για {population_size} άτομα αποθηκεύτηκαν.")

    return results

def main():
    print("BENCHMARK ΑΛΓΟΡΙΘΜΩΝ")
    print("=" * 60)

    print(f"Ημέρες: {config.DAYS}")
    print(f"Πλήρωμα ανά ημέρα: {config.CREW}")
    print(f"Μεγέθη πληθυσμού: {POPULATION_SIZES}")

    print("\nΈναρξη πειραματικής αξιολόγησης...")

    for population_size in POPULATION_SIZES:
        run_all_algorithms(population_size)

    print("\n" + "=" * 60)
    print("ΟΛΟΚΛΗΡΩΘΗΚΕ ΤΟ BENCHMARK")
    print(f"Αποτελέσματα: {RESULTS_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
