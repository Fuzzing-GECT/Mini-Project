import socket
import random
import time

ALPHABET = ["USER", "PASS", "LIST", "QUIT"]

class MealyMachine:
    def __init__(self):
        self.transitions = {}
        self.initial_state = 0

    def add_transition(self, state, symbol, next_state, output):
        if state not in self.transitions: self.transitions[state] = {}
        self.transitions[state][symbol] = (next_state, output)

    def simulate(self, input_sequence):
        state = self.initial_state
        outputs = []
        for symbol in input_sequence:
            if state in self.transitions and symbol in self.transitions[state]:
                next_state, output = self.transitions[state][symbol]
                outputs.append(output)
                state = next_state
            else:
                outputs.append("OFF") # Default for dead paths
        return outputs

def membership_query(sequence):
    # Small sleep to prevent OS socket exhaustion
    time.sleep(0.01)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect(("127.0.0.1", 2121))
        sock.recv(1024) 
        
        outputs = []
        alive = True
        for cmd in sequence:
            if not alive:
                outputs.append("OFF")
                continue
            try:
                sock.sendall((cmd + "\r\n").encode())
                data = sock.recv(1024)
                if not data:
                    alive = False
                    outputs.append("OFF")
                else:
                    # Capture only the 3-digit status code
                    outputs.append(data.decode().strip()[:3])
            except:
                alive = False
                outputs.append("OFF")
        sock.close()
        return outputs
    except:
        return ["OFF"] * len(sequence)

class LStarMealy:
    def __init__(self, alphabet):
        self.alphabet = alphabet
        self.S = [()]
        self.E = [()] # Start blind to force Equivalence Query
        self.row_cache = {}

    def table_entry(self, s, e):
        full = s + e
        if not full: return "INIT"
        return membership_query(full)[-1]

    def row(self, s):
        return tuple(self.table_entry(s, e) for e in self.E)

    def is_closed(self):
        S_rows = {self.row(s) for s in self.S}
        for s in self.S:
            for a in self.alphabet:
                sa = s + (a,)
                if self.row(sa) not in S_rows: return False, sa
        return True, None

    def is_consistent(self):
        for s1 in self.S:
            for s2 in self.S:
                if s1 != s2 and self.row(s1) == self.row(s2):
                    for a in self.alphabet:
                        if self.row(s1 + (a,)) != self.row(s2 + (a,)):
                            return False, (s1, s2, a)
        return True, None

    def build_hypothesis(self):
        hyp = MealyMachine()
        row_to_state = {}
        for s in self.S:
            r = self.row(s)
            if r not in row_to_state: row_to_state[r] = len(row_to_state)
        
        for s in self.S:
            curr = row_to_state[self.row(s)]
            for a in self.alphabet:
                out = self.table_entry(s, (a,))
                next_s = row_to_state[self.row(s + (a,))]
                hyp.add_transition(curr, a, next_s, out)
        return hyp

    def equivalence_query(self, hyp):
        print(f"EQ: Testing {len(hyp.transitions)} states...")
        for _ in range(150): # Increased test count
            test = tuple(random.choice(self.alphabet) for _ in range(random.randint(1, 8)))
            if membership_query(test) != hyp.simulate(test):
                print(f"!!! Counterexample: {test}")
                return test
        return None

    def run(self):
        while True:
            while True:
                closed, witness = self.is_closed()
                if not closed:
                    print(f"State {witness} is not closed.")
                    self.S.append(witness); continue
                consistent, witness = self.is_consistent()
                if not consistent:
                    s1, s2, a = witness
                    r1, r2 = self.row(s1+(a,)), self.row(s2+(a,))
                    for i, e in enumerate(self.E):
                        if r1[i] != r2[i]:
                            print(f"Rows {s1} and {s2} are inconsistent on input {a}. Adding suffix {(a,) + e} to E.")
                            self.E.append((a,) + e); break
                    continue
                break

            hyp = self.build_hypothesis()
            ce = self.equivalence_query(hyp)
            if not ce: return hyp
            for i in range(len(ce)):
                suffix = ce[i:]
                if suffix not in self.E: self.E.append(suffix)
def minimize_mealy(machine, alphabet):
        states = list(machine.transitions.keys())
    
        # Initial partition: group states by output behavior
        partitions = []
        output_map = {}
    
        for s in states:
          signature = tuple(machine.transitions[s][a][1] for a in alphabet)
          if signature not in output_map:
            output_map[signature] = []
          output_map[signature].append(s)
    
        partitions = list(output_map.values())
    
        changed = True
        while changed:
          changed = False
          new_partitions = []
    
          for group in partitions:
            subgroup_map = {}
    
            for state in group:
                signature = []
                for a in alphabet:
                    next_state = machine.transitions[state][a][0]
                    
                    # Find which partition next_state belongs to
                    for idx, part in enumerate(partitions):
                        if next_state in part:
                            signature.append(idx)
                            break
                
                signature = tuple(signature)
                
                if signature not in subgroup_map:
                    subgroup_map[signature] = []
                subgroup_map[signature].append(state)
            
            if len(subgroup_map) > 1:
                changed = True
            
            new_partitions.extend(subgroup_map.values())
        
          partitions = new_partitions
    
        # Build minimized machine
        minimized = MealyMachine()
        state_map = {}
    
        for idx, group in enumerate(partitions):
           for state in group:
             state_map[state] = idx
    
        for idx, group in enumerate(partitions):
           representative = group[0]
           for a in alphabet:
            next_state, output = machine.transitions[representative][a]
            minimized.add_transition(
                idx,
                a,
                state_map[next_state],
                output
            )
    
        return minimized


if __name__ == "__main__":
    learner = LStarMealy(ALPHABET)
    model = learner.run()

    print("\n--- BEFORE MINIMIZATION ---")
    for state, trans in model.transitions.items():
       print(f"State {state}: {trans}")

    min_model = minimize_mealy(model, ALPHABET)

    print("\n--- AFTER MINIMIZATION ---")
    for state, trans in min_model.transitions.items():
       print(f"State {state}: {trans}")
