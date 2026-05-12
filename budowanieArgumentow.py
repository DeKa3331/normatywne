class Rule:
    def __init__(self, rid, body, head, strict=False):
        self.id = rid
        self.body = body
        self.head = head
        self.strict = strict

    def __repr__(self):
        kind = '->' if self.strict else '=>'
        return f"{self.id}: {', '.join(self.body)} {kind} {self.head}"


class Argument:
    def __init__(self, aid, conclusion, premises, rules_used, subargs):
        self.id = aid
        self.conclusion = conclusion
        self.premises = premises
        self.rules_used = rules_used
        self.subargs = subargs

    def is_strict(self, kb, rules):
        for p in self.premises:
            if p not in kb:
                return False
        for rid in self.rules_used:
            if not rules[rid].strict:
                return False
        return True

    def is_hard(self, kh, rules):
        for p in self.premises:
            if p not in kh:
                return False
        for rid in self.rules_used:
            if not rules[rid].strict:
                return False
        return True

    def __repr__(self):
        return f"Arg({self.id}: {self.conclusion}; premises={sorted(self.premises)}; rules={self.rules_used})"


def negate(atom: str) -> str:
    atom = atom.strip()
    if atom.startswith('not '):
        return atom[4:]
    return 'not ' + atom


class ArgumentGenerator:
    def __init__(self, kh, kb, kp, rules):
        self.kh = kh
        self.kb = kb
        self.kp = kp
        self.rules = {r.id: r for r in rules}
        self.derived = {} #pogrupowane po konklizji
        self.arguments = [] #cala lista

    def _add_argument(self, arg: Argument) -> None:
        existing = self.derived.get(arg.conclusion, [])
        for e in existing:
            if e.premises == arg.premises and e.rules_used == arg.rules_used:
                return
        existing.append(arg)
        self.derived[arg.conclusion] = existing
        self.arguments.append(arg)

    def generate(self):
        aid = 1
        # baza faktów: najpierw hard, potem kb i kp (lists, bez duplikatów)
        combined = []
        for coll in (self.kh, self.kb, self.kp):
            for f in coll:
                if f not in combined:
                    combined.append(f)
        for f in sorted(combined):
            a = Argument(f"A{aid}", f, [f], [], [])
            self._add_argument(a)
            aid += 1

        changed = True
        while changed:
            changed = False
            for r in self.rules.values():
                if not r.body:
                    concl = r.head
                    arg = Argument(f"A{aid}", concl, [], [r.id], [])
                    existing = self.derived.get(concl, [])
                    if not any(e.premises == arg.premises and e.rules_used == arg.rules_used for e in existing):
                        self._add_argument(arg)
                        aid += 1
                        changed = True
                    continue

                lists_of_args = []
                possible = True
                for atom in r.body:
                    args_for_atom = self.derived.get(atom, [])
                    if not args_for_atom:
                        possible = False
                        break
                    lists_of_args.append(args_for_atom)

                if not possible:
                    continue

                for combo in cartesian_product(lists_of_args):
                    premises = []
                    subargs = []
                    rules_used = []
                    for sub in combo:
                        # merge premises (avoid duplicates)
                        for p in sub.premises:
                            if p not in premises:
                                premises.append(p)
                        subargs.append(sub)
                        rules_used += sub.rules_used
                    rules_used = rules_used + [r.id]
                    concl = r.head
                    arg = Argument(f"A{aid}", concl, premises, rules_used, subargs)
                    existing = self.derived.get(concl, [])
                    if not any(e.premises == arg.premises and e.rules_used == arg.rules_used for e in existing):
                        self._add_argument(arg)
                        aid += 1
                        changed = True

        return self.arguments

    def detect_attacks(self):
        attacks = []
        for a in self.arguments:
            for b in self.arguments:
                if a.id == b.id: #sam ze soba
                    continue
                if a.conclusion == negate(b.conclusion): #negacje konkluzji -> rebuttal
                    attacks.append(('rebuttal', a.id, b.id))
                    continue
                if a.conclusion.startswith('not '): # undercut if conclusion negates a premise
                    p = a.conclusion[4:]
                    if p in b.premises:
                        attacks.append(('undercut', a.id, b.id))
                        continue
                    # or undercut if conclusion negates a rule used by b (e.g. 'not r3')
                    if p in b.rules_used:
                        attacks.append(('undercut', a.id, b.id))
                        continue
        return attacks


def cartesian_product(lists_of_lists):
    if not lists_of_lists:
        return [()]
    res = [[]]
    for lst in lists_of_lists:
        new = []
        for prefix in res:
            for item in lst:
                new.append(prefix + [item])
        res = new
    return res

#wejście [[A1, A2], [B1, B2]]
#wyjście [[A1, B1], [A1, B2], [A2, B1], [A2, B2]]


def export_argumentation_framework(filename, arguments, attacks):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('argumenty: ')
        f.write(', '.join(arg.id for arg in arguments))
        f.write('\n')

        for _, attacker, attacked in attacks:
            f.write(f'{attacker} -> {attacked}\n')


def parse_input_file(filename):
    kh = []
    kb = []
    kp = []
    rules = []
    rid_counter = 1

    current_section = None

    def parse_atoms(part):
        res = []
        for x in part.split(','):
            v = x.strip()
            if v:
                res.append(v)
        return res

    with open(filename, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue

            low = line.lower()
            # section headers
            if low.startswith('l:'):
                # list of all atoms (not used directly, but parse for completeness)
                part = line.split(':', 1)[1]
                # ignore for now
                current_section = 'L'
                continue
            if low.startswith('kh:'):
                part = line.split(':', 1)[1]
                for v in parse_atoms(part):
                    if v not in kh:
                        kh.append(v)
                current_section = 'kh'
                continue
            if low.startswith('kb:'):
                part = line.split(':', 1)[1]
                for v in parse_atoms(part):
                    if v not in kb:
                        kb.append(v)
                current_section = 'kb'
                continue
            if low.startswith('kp:'):
                part = line.split(':', 1)[1]
                for v in parse_atoms(part):
                    if v not in kp:
                        kp.append(v)
                current_section = 'kp'
                continue

            if low.startswith('rs:'):
                current_section = 'Rs'
                continue
            if low.startswith('rd:'):
                current_section = 'Rd'
                continue

            # inside Rs / Rd sections we expect rule lines
            if current_section in ('Rs', 'Rd') or '->' in line or '=>' in line:
                # find operator
                op = None
                if '->' in line:
                    op = '->'
                elif '=>' in line:
                    op = '=>'
                if op is None:
                    continue

                left, right = line.split(op, 1)
                left = left.strip()
                head = right.strip()

                # normalize negation marker: '~x' -> 'not x'
                if head.startswith('~'):
                    head = 'not ' + head[1:].strip()

                # left may contain rule id before ':'
                if ':' in left:
                    rid_part, body_part = left.split(':', 1)
                    rid = rid_part.strip()
                    body_text = body_part.strip()
                else:
                    rid = f"r{rid_counter}"
                    rid_counter += 1
                    body_text = left

                body = []
                if body_text:
                    for v in parse_atoms(body_text):
                        # normalize negation in body too: ~x -> 'not x'
                        vv = v
                        if vv.startswith('~'):
                            vv = 'not ' + vv[1:].strip()
                        body.append(vv)

                strict = (op == '->')
                rules.append(Rule(rid, body, head, strict=strict))
                continue

            # fallback: ignore unknown lines

    return kh, kb, kp, rules


def main():
    # prefer reading 'baza-argumentow.bw' if present, fall back to 'arguments.bw'
    try:
        try:
            kh, kb, kp, rules = parse_input_file('baza-argumentow.bw')
            if not kh and not kb and not kp and not rules:
                raise FileNotFoundError
        except FileNotFoundError:
            kh, kb, kp, rules = parse_input_file('arguments.bw')
            if not kh and not kb and not kp and not rules:
                raise FileNotFoundError
    except FileNotFoundError:
        kb = ['e']
        kp = ['a', 'b', 'c', 'd']
        rules = [
            Rule('r1', ['a', 'b'], 'g', strict=False),
            Rule('r2', ['c'], 'g', strict=False),
            Rule('r3', ['c', 'd'], 'h', strict=True),
            Rule('r4', [], 'a', strict=True),
        ]

        kh = []

    gen = ArgumentGenerator(kh, kb, kp, rules)
    args = gen.generate()

    print('Wygenerowane argumenty:')
    for arg in args:
        s = arg.is_strict(kb, gen.rules)
        print(arg, 'STRICT' if s else '')

    attacks = gen.detect_attacks()
    print('\nWykryte ataki:')
    for t, a, b in attacks:
        print(f"{t}: {a} -> {b}")

    export_argumentation_framework('baza-atakow.bw', args, attacks)
    print('\nZapisano do pliku: baza-atakow.bw')


if __name__ == '__main__':
    main()
