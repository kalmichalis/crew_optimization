
from core import data
from algorithms.milp import solve_milp
from core.rules import rules_errors
from core.scoring import score


# ---------- Αρχικοποίηση dummy δεδομένων ----------

m, mech, elec = data.dummy_members()
data.setup(m, mech, elec)


# ---------- Εκτέλεση MILP ----------

sched, results = solve_milp()


# ---------- Έλεγχος αποτελεσμάτων ----------

print("\n========== MILP RESULTS ==========")

for title, value, status in results:
    print(f"{title}: {value} | {status}")


# ---------- Έλεγχος κανόνων ----------

errors = rules_errors(sched)

print("\n========== RULE VALIDATION ==========")

if errors:
    print(f"Βρέθηκαν {len(errors)} παραβιάσεις:")

    for error in errors:
        print(error)
else:
    print("Η λύση είναι έγκυρη. Δεν υπάρχουν παραβιάσεις.")


# ---------- Λεξικογραφική βαθμολογία ----------

print("\n========== MILP SCORE ==========")
print(score(sched))
