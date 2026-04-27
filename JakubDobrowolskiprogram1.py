def clean(text):
    text = text.strip()
    is_negated = text.startswith("~")

    if is_negated:
        text = text[1:].strip()

    text = text.strip('"')

    if is_negated:
        return "~" + text
    return text

class Rule:
    def __init__(self, conditions, result, number):
        self.conditions = conditions
        self.result = result
        self.number = number

    def can_apply(self, facts):
        for cond in self.conditions:
            if cond.startswith("~"):
                fact = cond[1:] #usuwam ~ 
                if fact in facts:
                    return False
            else:
                if cond not in facts:
                    return False
        return True

    def apply(self, facts):
        if self.result not in facts:
            facts.append(self.result)


def parse_rule(line):
    num, rest = line.split(":", 1)
    left, right = rest.split("->")

    conditions = [clean(c) for c in left.split("&&")]
    result = clean(right)

    return Rule(conditions, result, int(num))




rules = []
facts = []
target= None



with open("baza-wiedzy-samochod-negcje.bw", "r", encoding="utf-8") as f:
#with open("baza-wiedzy-samochod.bw", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):  #lubie komentarze
            continue
        if not line.endswith('"'): #zasady musza sie konczyc na ", nie wywale programu przy bledach w pliku tylko sobie pomine
           continue

        if line.startswith("Fakty"):
            part = line.split(":", 1)[1] #usuwam "Fakty:"
            facts = [clean(x) for x in part.split(",")]
        elif line.startswith("Cel"):
            part = line.split(":", 1)[1]  # usuwam "Cel:"
            target = clean(part)
        else:
            rules.append(parse_rule(line))

def backward_chain(goal, facts, rules, visited=None):
    if visited is None: #anty petla
        visited = []

    if goal.startswith("~"):
        fact_to_negate = goal[1:] #usuwamy ~
        test_facts = facts.copy()
        positive_rules = [r for r in rules if not any(c.startswith("~") for c in r.conditions)]
        return not backward_chain(fact_to_negate, test_facts, positive_rules, visited=[])

    if goal in facts:
        return True

    if goal in visited:
        return False
    visited.append(goal)

    applicable_rules = [r for r in rules if r.result == goal]

    for rule in applicable_rules:
        if all(backward_chain(cond, facts, rules, visited) for cond in rule.conditions):
            #print(f"Reguła {rule.number} potrzebna '{goal}'")
            if goal not in facts:
                facts.append(goal)
            return True
        else:
           # print(f"Reguła {rule.number} nie potrzebna '{goal}'")
            print("\n")
    return False


#backward podsumowanie
if target:
    if backward_chain(target, facts, rules):
        print(f"\nCel '{target}' jest mozliwy.\n")
    else:
        print(f"\nCel '{target}' NIE mozliwy.\n")


changed = True

while changed:
    changed = False
    for rule in rules:
        if rule.can_apply(facts) and rule.result not in facts:
            print(f"prawidlowa regula: {rule.number} -> {rule.result}")
            rule.apply(facts)
            changed = True



wyswietl_wszystkie = False
if wyswietl_wszystkie:
    print("\nWszystkie fakty:")
    for i, fact in enumerate(facts, start=1):
        print(f"{i}:{fact}")

