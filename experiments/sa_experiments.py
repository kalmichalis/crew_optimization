
import random
from algorithms.simulated_annealing import lexicographic_cost
from core import data
from core.rules import rules_errors

from algorithms.simulated_annealing import (
    solve_sa,
    create_initial_solution,
    create_neighbor,
    create_neighbor_smart,
    create_neighbor_swap
)


# ==================================================
# 1. ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ
# ==================================================

m, mech, elec = data.dummy_members()
data.setup(m, mech, elec)


def test_lexicographic_encoding(samples=10_000, seed=42):

    rng = random.Random(seed)

    print("\n=== ΕΛΕΓΧΟΣ ΛΕΞΙΚΟΓΡΑΦΙΚΗΣ ΚΩΔΙΚΟΠΟΙΗΣΗΣ ===")

    for i in range(samples):

        score_a = (
            0,
            rng.randint(0, 155),
            rng.randint(0, 1_212_720),
            rng.randint(0, 25),
            rng.randint(0, 600),
            rng.randint(0, 240),
            rng.randint(0, 25),
            rng.randint(0, 600)
        )

        score_b = (
            0,
            rng.randint(0, 155),
            rng.randint(0, 1_212_720),
            rng.randint(0, 25),
            rng.randint(0, 600),
            rng.randint(0, 240),
            rng.randint(0, 25),
            rng.randint(0, 600)
        )

        cost_a = lexicographic_cost(score_a)
        cost_b = lexicographic_cost(score_b)

        if (score_a < score_b) != (cost_a < cost_b):
            print("ΑΠΟΤΥΧΙΑ!")
            print("Score A:", score_a)
            print("Score B:", score_b)
            print("Cost A:", cost_a)
            print("Cost B:", cost_b)
            return False

    print(f"Επιτυχία: {samples:,} ζεύγη ελέγχθηκαν.")
    print("Η λεξικογραφική σειρά διατηρείται.")

    return True
test_lexicographic_encoding()
from core import config

print("\n=== ΕΛΕΓΧΟΣ ΟΡΙΩΝ SCORE ===")
print("DAYS:", config.DAYS)
print("CREW:", config.CREW)
print("N:", data.N)
print("MAX ORDER:", max(data.ORDER.values()))
print("HOLIDAYS:", len(config.HOLIDAYS))
print("MAX ASSIGNMENTS:", config.DAYS * config.CREW)

# ==================================================
# 2. ΣΥΓΚΡΙΣΗ SIMULATED ANNEALING
# ==================================================

experiments = [
    ("ORIGINAL NEIGHBOR", create_neighbor),
    ("SWAP NEIGHBOR", create_neighbor_swap)
]

results = {}

for name, neighbor_function in experiments:

    print(f"\n{'=' * 50}")
    print(f"SIMULATED ANNEALING: {name}")
    print(f"{'=' * 50}")

    sched, sa_score = solve_sa(
        iterations_per_temp=100,
        max_levels=100,
        alpha=0.95,
        neighbor_fn=neighbor_function
    )

    errors = rules_errors(sched)

    results[name] = {
        "schedule": sched,
        "score": sa_score,
        "errors": errors
    }

    print(f"\n=== ΑΠΟΤΕΛΕΣΜΑ {name} ===")
    print("Βαθμολογία:", sa_score)
    print("Ημέρες:", len(sched))
    print("Παραβιάσεις:", len(errors))

    if not errors:
        print("ΕΠΙΤΥΧΙΑ: Έγκυρο πρόγραμμα.")
    else:
        print("ΑΠΟΤΥΧΙΑ: Υπάρχουν παραβιάσεις.")


# ==================================================
# 3. ΚΟΙΝΗ ΑΡΧΙΚΗ ΛΥΣΗ ΓΙΑ ΤΑ TESTS
# ==================================================

print("\n=== ΔΗΜΙΟΥΡΓΙΑ ΑΡΧΙΚΗΣ ΛΥΣΗΣ ===")

rng = random.Random(42)

initial = create_initial_solution(rng)

print("Αρχικές παραβιάσεις:", len(rules_errors(initial)))


# ==================================================
# 4. ΣΥΓΚΡΙΣΗ NEIGHBOR FUNCTIONS
# ==================================================

def check_neighbor(name, function, sched, seed=42):

    rng = random.Random(seed)

    valid = 0
    unchanged = 0

    for _ in range(1000):

        neighbor = function(sched, rng)

        if neighbor == sched:
            unchanged += 1

        elif not rules_errors(neighbor):
            valid += 1

    print(f"\n=== {name} ===")
    print("Έγκυρες νέες λύσεις:", valid)
    print("Μη έγκυρες / χωρίς αλλαγή:", unchanged)
    print("Ποσοστό έγκυρων:", round(valid / 1000 * 100, 2), "%")


check_neighbor(
    "ORIGINAL NEIGHBOR",
    create_neighbor,
    initial
)

check_neighbor(
    "SMART NEIGHBOR",
    create_neighbor_smart,
    initial
)

check_neighbor(
    "SWAP NEIGHBOR",
    create_neighbor_swap,
    initial
)
