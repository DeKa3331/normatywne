def clean(text):
    text = text.strip()
   # text = text.strip('"')
    return text

def is_subset(smaller, bigger):
    for arg in smaller:
        if arg not in bigger:
            return False
    return True


class Attack:
    def __init__(self, attacker, attacked):
        # Relacja ataku: attacker -> attacked.
        self.attacker = clean(attacker)
        self.attacked = clean(attacked)
    
    def __repr__(self):
        return f"{self.attacker} -> {self.attacked}"


class ArgumentationFramework:
    def __init__(self):
        # attacks: lista relacji ataku, arguments: wszystkie argumenty w systemie.
        self.attacks = []
        self.arguments = []
    
    def load_attacks_from_file(self, filename):    
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue

                    if line.lower().startswith('argumenty:'):
                        part = line.split(':', 1)[1]
                        for raw_arg in part.split(','):
                            arg = clean(raw_arg)
                            if arg and arg not in self.arguments:
                                self.arguments.append(arg)
                        continue
                    
                    if '->' in line:
                        parts = line.split('->')
                        if len(parts) == 2:
                            attacker = clean(parts[0])
                            attacked = clean(parts[1])
                            
                            attack = Attack(attacker, attacked)
                            self.attacks.append(attack)
                            
                            # Upewnij się, że oba argumenty istnieją w liście argumentów.
                            if attacker not in self.arguments:
                                self.arguments.append(attacker)
                            if attacked not in self.arguments:
                                self.arguments.append(attacked)
        
        except FileNotFoundError:
            print(f"Błąd: Nie można otworzyć pliku {filename}")
    
    def get_attackers(self, argument):
        # Zwraca listę argumentów, które atakują podany argument.
        attackers = []
        for attack in self.attacks:
            if attack.attacked == argument:
                attackers.append(attack.attacker)
        return attackers
    
    def is_attacked_by_set(self, argument, extension):
        # Sprawdza, czy którykolwiek argument z extension atakuje podany argument.
        attackers = self.get_attackers(argument)
        for attacker in attackers:
            if attacker in extension:
                return True
        return False
    
    def is_acceptable(self, argument, extension):
        # Argument jest akceptowalny względem extension, jeśli każdy jego atakujący
        # jest kontratakowany przez co najmniej jeden argument z extension.
        attackers = self.get_attackers(argument)
        
        if not attackers:
            return True
        
        for attacker in attackers: #sprawdzenie kazdego atakujacego
            if not self.is_attacked_by_set(attacker, extension):
                return False
        
        return True
    
    def is_admissible(self, extension):
        # Extension jest dopuszczalna, gdy:
        # 1) każdy argument w extension jest akceptowalny,
        # 2) extension jest bezkonfliktowa (brak ataku wewnątrz zbioru).
        for arg in extension:
            if not self.is_acceptable(arg, extension):
                return False
        
        for attack in self.attacks:
            if attack.attacker in extension and attack.attacked in extension:
                return False
        
        return True


def find_all_preferred_extensions(af):
    # Preferred extensions = maksymalne (w sensie inkluzji) zbiory dopuszczalne.
    if not af.arguments:
        return []
    
    all_subsets = []
    arguments_list = list(af.arguments)
    n = len(arguments_list)
    
    # Generuje wszystkie możliwe podzbiory argumentów (brute force).
    for i in range(2**n):
        subset = []
        for j in range(n):
            if i & (1 << j):
                subset.append(arguments_list[j])
        all_subsets.append(subset)
    
    admissible_sets = []
    for subset in all_subsets:
        if af.is_admissible(subset):
            admissible_sets.append(subset)


    
    # Zostaw tylko te dopuszczalne zbiory, które nie są podzbiorem większego.
    preferred = []
    for candidate in admissible_sets:
        has_larger_container = False
        for other_set in admissible_sets:
            if len(candidate) < len(other_set) and is_subset(candidate, other_set):
                has_larger_container = True
                break
        if not has_larger_container:
            preferred.append(candidate)
    
    return preferred


def find_grounded_extension(af):
    # Iteracyjne wyznaczanie grounded extension jako punktu stałego operatora
    # akceptowalności (zaczynamy od pustego zbioru).
    current = []

    while True:
        next_extension = []
        for arg in af.arguments:
            if af.is_acceptable(arg, current):
                next_extension.append(arg)

        next_extension = sorted(next_extension)
        if current == next_extension:
            return next_extension

        current = next_extension


af = ArgumentationFramework()
af.load_attacks_from_file('baza-atakow.bw')
preferred_extensions = find_all_preferred_extensions(af)
grounded_extension = find_grounded_extension(af)
ataki=False

if ataki:
    print("Wczytane ataki:")
    for attack in af.attacks:
        print(f"{attack}")
    print(f"\nArgumenty w systemie: {sorted(af.arguments)}")
    print(f"Liczba preferowanych ekstensji: {len(preferred_extensions)}\n")





for i, ext in enumerate(preferred_extensions, 1):
    print(f"Ekstensja {i}: {sorted(ext)}")

print(f"\nGrounded: {grounded_extension}")







tests = False

if tests:
    print()
    for i, ext in enumerate(preferred_extensions, 1):
        print(f"Ekstensja {i}:")
        
        acceptable = []
        not_acceptable = []
        
        for arg in sorted(af.arguments):
            if arg in ext:
                acceptable.append(arg)
            else:
                not_acceptable.append(arg)
        
        print(f"Akceptowalne: {acceptable}")
        print(f"Nieakceptowalne: {not_acceptable}")
        print()