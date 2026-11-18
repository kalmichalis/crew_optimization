
import time
import statistics

from core import data
from core.rules import rules_errors
from algorithms.simulated_annealing import solve_sa, create_neighbor


# ---------------------------------------------------------
# 1. ΑΡΧΙΚΟΠΟΙΗΣΗ ΔΕΔΟΜΕΝΩΝ
# ---------------------------------------------------------

# Χρησιμοποιούμε τα ίδια συνθετικά δεδομένα σε όλες τις εκτελέσεις.
members, mech, elec = data.dummy_members()
data.setup(members, mech, elec)


# ---------------------------------------------------------
# 2. ΠΑΡΑΜΕΤΡΟΙ ΠΕΙΡΑΜΑΤΟΣ
# ---------------------------------------------------------

alpha = 0.90
iterations_per_temp = 100
max_levels = 200

# Πέντε διαφορετικά seeds για ανεξάρτητες εκτελέσεις.
seeds = [42, 123, 456, 789, 2026]


# ---------------------------------------------------------
# 3. ΕΚΤΕΛΕΣΗ ΠΕΙΡΑΜΑΤΩΝ
# ---------------------------------------------------------

results = []

for seed in seeds:

    print("\n" + "=" * 55)
    print(f"ΠΕΙΡΑΜΑ ΜΕ SEED = {seed}")
    print("=" * 55)

    start_time = time.perf_counter()

    # Εκτέλεση του Simulated Annealing.
    best_schedule, best_score = solve_sa(
        iterations_per_temp=iterations_per_temp,
        max_levels=max_levels,
        alpha=alpha,
        neighbor_fn=create_neighbor,
        seed=seed
    )

    elapsed_time = time.perf_counter() - start_time

    # Έλεγχος εγκυρότητας της καλύτερης λύσης.
    violations = rules_errors(best_schedule)

    # Αποθήκευση αποτελεσμάτων.
    results.append({
        "seed": seed,
        "score": best_score,
        "time": elapsed_time,
        "violations": len(violations)
    })


# ---------------------------------------------------------
# 4. ΣΥΓΚΕΝΤΡΩΤΙΚΗ ΑΞΙΟΛΟΓΗΣΗ
# ---------------------------------------------------------

# Συγκεντρώνουμε τις τιμές του Distribution.
distributions = [r["score"][2] for r in results]

# Συγκεντρώνουμε τους χρόνους εκτέλεσης.
times = [r["time"] for r in results]

print("\n\n")
print("=" * 75)
print("ΣΥΓΚΕΝΤΡΩΤΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΑ SIMULATED ANNEALING")
print("=" * 75)

print(
    f"{'Seed':<12}"
    f"{'Over-capacity':<18}"
    f"{'Distribution':<18}"
    f"{'Χρόνος (sec)':<15}"
    f"{'Παραβιάσεις':<12}"
)

print("-" * 75)

for r in results:

    print(
        f"{r['seed']:<12}"
        f"{r['score'][1]:<18}"
        f"{r['score'][2]:<18}"
        f"{r['time']:<15.2f}"
        f"{r['violations']:<12}"
    )


# ---------------------------------------------------------
# 5. ΣΤΑΤΙΣΤΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΩΝ
# ---------------------------------------------------------

print("\n" + "=" * 55)
print("ΣΤΑΤΙΣΤΙΚΗ ΑΝΑΛΥΣΗ")
print("=" * 55)

print(f"Καλύτερο Distribution: {min(distributions)}")
print(f"Μέσο Distribution:     {statistics.mean(distributions):.2f}")
print(f"Χειρότερο Distribution:{max(distributions)}")

print(f"\nΜέσος χρόνος:          {statistics.mean(times):.2f} sec")
print(f"Ελάχιστος χρόνος:      {min(times):.2f} sec")
print(f"Μέγιστος χρόνος:       {max(times):.2f} sec")

print(f"\nΈγκυρες λύσεις:        {sum(r['violations'] == 0 for r in results)}/{len(results)}")
