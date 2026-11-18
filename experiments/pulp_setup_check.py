# Εισαγωγή της βιβλιοθήκης PuLP
import pulp

# Εμφάνιση της εγκατεστημένης έκδοσης
print("PuLP version:", pulp.__version__)

# Δημιουργία ενός απλού προβλήματος ελαχιστοποίησης
model = pulp.LpProblem("Test_MILP", pulp.LpMinimize)

# Δημιουργία μιας ακέραιας μεταβλητής
x = pulp.LpVariable("x", lowBound=0, cat="Integer")

# Αντικειμενική συνάρτηση: ελαχιστοποίηση του x
model += x

# Περιορισμός: x >= 5
model += x >= 5

# Επίλυση με τον CBC
model.solve(pulp.PULP_CBC_CMD(msg=False))

# Εμφάνιση αποτελεσμάτων
print("Solver status:", pulp.LpStatus[model.status])
print("Optimal x:", pulp.value(x))