import socket
import random
import time

# --- CONFIGURATION ---
# Use 'anonymous' for vsftpd. Port 21 is default for Ubuntu.
ALPHABET = ["USER anonymous", "PASS guest", "PWD", "QUIT"]
TARGET_IP = "127.0.0.1"
TARGET_PORT = 21

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
            if state in self.transitions and symbol in self.transitions.get(state, {}):
                next_state, output = self.transitions[state][symbol]
                outputs.append(output)
                state = next_state
            else:
                outputs.append("OFF")
        return outputs

    def export_dot(self, filename):
        dot = ["digraph Mealy {", '  rankdir=LR;', '  node [shape=circle];']
        # Color coding for FTP codes
        colors = {"230": "green", "530": "red", "331": "orange", "221": "blue"}
        for state, transitions in self.transitions.items():
            for cmd, (next_state, output) in transitions.items():
                color = colors.get(output, "black")
                label = f"{cmd} / {output}"
                dot.append(f'  {state} -> {next_state} [label="{label}", color="{color}", fontcolor="{color}"];')
        dot.append("}")
        with open(filename, "w") as f:
            f.write("\n".join(dot))

def membership_query(sequence):
    """The Teacher: Physically talks to vsftpd on Ubuntu."""
    time.sleep(0.02) # Prevent socket flooding
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((TARGET_IP, TARGET_PORT))
        sock.recv(1024) # Greeting 220
        
        outputs = []
        alive = True
        for cmd in sequence:
            if not alive:
                outputs.append("OFF")
                continue
            try:
                sock.sendall((cmd + "\r\n").encode())
                data = sock.recv(1024).decode(errors='ignore').strip()
                if not data:
                    alive = False
                    outputs.append("OFF")
                else:
                    # Capture the 3-digit status code (e.g., 230, 331)
                    outputs.append(data[:3])
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
        self.E = [()] 
        self.mq_cache = {}

    def table_entry(self, s, e):
        full = s + e
        if not full: return "INIT"
        if full not in self.mq_cache:
            self.mq_cache[full] = membership_query(full)
        return self.mq_cache[full][-1]

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
        unique_rows = {}
        for s in self.S:
            r = self.row(s)
            if r not in unique_rows: unique_rows[r] = len(unique_rows)
        
        for s in self.S:
            curr_id = unique_rows[self.row(s)]
            for a in self.alphabet:
                out = self.table_entry(s, (a,))
                next_id = unique_rows[self.row(s + (a,))]
                hyp.add_transition(curr_id, a, next_id, out)
        
        hyp.initial_state = unique_rows[self.row(())]
        return hyp

    def equivalence_query(self, hyp):
        print(f"[*] EQ: Testing Hypothesis with {len(hyp.transitions)} states...")
        for _ in range(50): # Reduced for network speed
            test = tuple(random.choice(self.alphabet) for _ in range(random.randint(1, 5)))
            if membership_query(test) != hyp.simulate(test):
                return test
        return None

    def run(self):
        while True:
            while True:
                closed, witness = self.is_closed()
                if not closed:
                    self.S.append(witness); continue
                consistent, witness = self.is_consistent()
                if not consistent:
                    s1, s2, a = witness
                    r1, r2 = self.row(s1+(a,)), self.row(s2+(a,))
                    for i, e in enumerate(self.E):
                        if r1[i] != r2[i]:
                            self.E.append((a,) + e); break
                    continue
                break

            hyp = self.build_hypothesis()
            ce = self.equivalence_query(hyp)
            if not ce: return hyp
            # Add counterexample and prefixes to S
            for i in range(1, len(ce) + 1):
                prefix = ce[:i]
                if prefix not in self.S: self.S.append(prefix)

if __name__ == "__main__":
    print("[!] Starting Real-World L* Learning on Port 21...")
    learner = LStarMealy(ALPHABET)
    model = learner.run()
    
    model.export_dot("ftp_learned_model_off.dot")
    print("[+] Done! Run: dot -Tpng ftp_learned_model.dot -o model.png && xdg-open model.png")
