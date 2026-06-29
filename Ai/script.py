import csv

parents = {
            1: "graphs",
            2: "shortest paths",
            3: "trees",
            4: "dp",
            5: "greedy",
            6: "binary search",
            7: "two pointers",
            8: "strings",
            9: "sortings",
            10: "data structures",
            11: "math",
            12: "number theory",
            13: "combinatorics",
            14: "bitmasks",
            15: "geometry",
            16: "probabilities",
            17: "flows",
            18: "implementation",
            19: "string suffix structures",
            20: "advanced queries",
            21: "divide and conquer",
            22: "constructive algorithms",
            23: "games",
            24:"brute force"
        }

# Child concepts organized by parent
children = {
    1: [(101, "Graph Representation", "Beginner"), (102, "BFS", "Intermediate"),
        (103, "DFS", "Intermediate"), (104, "Connected Components", "Intermediate"),
        (105, "Cycle Detection", "Intermediate"), (106, "Topological Sort", "Advanced"),
        (107, "Strongly Connected Components", "Advanced"), (108, "Bipartite Graph Check", "Intermediate"),
        (109, "2-sat", "Advanced"),
        (110, "graphs matching", "Expert")
        ],

    2: [(201, "Dijkstra", "Advanced"), (202, "Bellman-Ford", "Advanced"),
        (203, "Floyd-Warshall", "Advanced"), (204, "0-1 BFS", "Advanced"),
        (205, "Shortest Path in DAG", "Advanced")],

    3: [(301, "Tree DFS", "Intermediate"), (302, "Tree DP", "Advanced"),
        (303, "Lowest Common Ancestor", "Advanced"), (304, "Binary Lifting", "Expert"),
        (305, "Tree Diameter", "Intermediate")],

    4: [(401, "1D DP", "Intermediate"), (402, "2D DP", "Intermediate"),
        (403, "Knapsack", "Intermediate"), (404, "Longest Increasing Subsequence", "Intermediate"),
        (405, "Longest Common Subsequence", "Intermediate"), (406, "Edit Distance", "Advanced"),
        (407, "Bitmask DP", "Advanced"), (408, "Digit DP", "Advanced"),
        (409, "Tree DP", "Advanced"), (410, "Interval DP", "Advanced"),
        (411, "DP on DAG", "Advanced")],

    5: [(501, "Activity Selection", "Intermediate"), (502, "Interval Scheduling", "Intermediate"),
        (503, "Greedy Sorting", "Intermediate")],

    6: [(601, "Binary Search on Array", "Intermediate"), (602, "Binary Search on Answer", "Advanced"),
        (603, "ternary search", "Advanced")],

    7: [(701, "Sliding Window", "Intermediate"), (702, "Two Pointers on Sorted Array", "Intermediate")],

    8: [(801, "String Matching", "Intermediate"), (802, "KMP", "Advanced"),
        (803, "Z Algorithm", "Advanced"), (804, "Prefix Function", "Advanced"),
        (805, "Trie", "Intermediate"), (806, "Palindrome Detection", "Intermediate"),
        (807, "hashing", "Advanced")],

    9: [(901, "Custom Comparator Sorting", "Intermediate"), (902, "Coordinate Compression", "Intermediate")],

    10: [(1001, "Stack", "Beginner"), (1002, "Queue", "Beginner"),
            (1003, "Deque", "Intermediate"), (1004, "Priority Queue", "Intermediate"),
            (1005, "dsu", "Advanced"), (1006, "Fenwick Tree", "Advanced"),
            (1007, "Segment Tree", "Advanced"), (1008, "Lazy Segment Tree", "Expert"),
            (1009, "Sparse Table", "Advanced"), (1010, "Ordered Set", "Advanced"),
            (1011, "Hash Map", "Intermediate"), (1012, "Multiset", "Intermediate"),
            (1013, "Monotonic Stack", "Advanced"), (1014, "Monotonic Queue", "Advanced"),
            (1015, "Sqrt Decomposition", "Advanced")],

    11: [(1101, "GCD", "Beginner"), (1102, "LCM", "Beginner"),
            (1103, "Modular Arithmetic", "Intermediate"), (1104, "Modular Inverse", "Advanced"),
            (1105, "Fast Exponentiation", "Intermediate"), (1106, "Divisors", "Intermediate"),
            (1107, "Difference Array", "Intermediate"),
            (1110, "Complex Numbers", "Advanced"),
            (1111, "matrices", "Advanced")],

    12: [(1201, "Prime Sieve", "Intermediate"), (1202, "Prime Factorization", "Intermediate"),
            (1203, "chinese remainder theorem", "Expert")],

    13: [(1301, "Permutations", "Intermediate"), (1302, "Combinations", "Intermediate"),
            (1303, "Pascal Triangle", "Intermediate"), (1304, "Inclusion-Exclusion", "Advanced"),
            (1305, "Modular Combinations", "Advanced")],

    14: [(1401, "Bitmask Enumeration", "Intermediate"), (1402, "Submask Enumeration", "Advanced")],

    15: [(1501, "Distance Between Points", "Beginner"), (1502, "Orientation Test", "Intermediate"),
            (1503, "Line Intersection", "Advanced"), (1504, "Polygon Area", "Intermediate"),
            (1505, "Convex Hull", "Expert"), (1506, "Rotating Calipers", "Expert"),
            (1507, "Sweep Line", "Expert")],

    16: [(1601, "Expected Value", "Advanced"), (1602, "Conditional Probability", "Advanced")],

    17: [(1701, "Max Flow", "Expert"), (1702, "Min Cut", "Expert"),
            (1703, "Bipartite Matching", "Expert"), (1704, "Min Cost Max Flow", "Expert")],

    18: [(1801, "Simulation", "Beginner"), (1802, "Brute Force Enumeration", "Beginner"),
            (1803, "Recursion", "Intermediate"), (1804, "Backtracking", "Intermediate"),
            (1805, "State Simulation", "Intermediate"), (1806, "Prefix Sum", "Intermediate")],

    19: [(1901, "Suffix Array", "Expert"), (1902, "Suffix Automaton", "Expert")],

    20: [(2001, "Mo's Algorithm", "Expert")],

    21: [(2101, "fft", "Expert"), (2102, "Meet-in-the-middle", "Advanced")],
    22: [(2201, "Constructive Techniques", "Intermediate"), (2202, "Schedules", "Intermediate"),
            (2203, "expression parsing", "Advanced"), (2204, "interactive", "Advanced")],
    23: [(2301, "Game Theory Basics", "Intermediate")],
}

# Prerequisites: concept -> list of (prerequisite_id, weight)
# Weight: 0.5-0.95 represents closeness/importance
# FIXED: Similar concepts have HIGHER weights, unrelated have LOWER weights
prerequisites = {
    # ============ PARENT PREREQUISITES ============
    2: [(1, 0.95)],  # Shortest paths ← Graphs (critical)
    3: [(1, 0.90), (10, 0.70)],  # Trees ← Graphs (critical) + DS (useful)
    4: [(1803, 0.90), (10, 0.70),(24,0.90)],  # DP ← Recursion + DS+ brute force
    5: [(9, 0.85),(24,0.85)],  # Greedy ← Sorting (related approach)+ brute force
    6: [(9, 0.95)],  # Binary Search ← Sorting (requires sorted)
    7: [(10, 0.85)],  # Two Pointers ← Data Structures
    8: [(10, 0.80)],  # Strings ← DS (uses DS)
    12: [(11, 0.95)],  # Number Theory ← Math (critical)
    13: [(11, 0.95)],  # Combinatorics ← Math (critical)
    14: [(11, 0.85), (24,0.85)],  # Bitmasks ← Math (bitwise operations)+ brute force
    16: [(13, 0.90)],  # Probabilities ← Combinatorics (related)
    17: [(1, 0.95), (2, 0.85)],  # Flows ← Graphs + Shortest Paths (critical)
    19: [(8, 0.95), (9, 0.80), (6, 0.75)],  # String Suffix ← Strings (critical)
    20: [(10, 0.95), (7, 0.90), (9, 0.85)],  # Advanced Queries ← DS + Two Pointers
    21: [(4, 0.85), (1, 0.70)],  # Divide & Conquer ← DP + Graphs
    22: [(18, 0.85)],  # Constructive ← Implementation
    23: [(13, 0.90), (11, 0.85)],  # Game Theory ← Combinatorics + Math
    24:[(18, 0.95), (11, 0.70)], #brute force<-implementation +math

    # ============ CHILD PREREQUISITES - SAME PARENT (HIGH WEIGHT) ============
    # BFS & DFS siblings - VERY CLOSELY RELATED
    102: [(101, 0.95)],  # BFS ← Graph Representation
    103: [(101, 0.95)],  # DFS ← Graph Representation
    104: [(102, 0.92), (103, 0.92)],  # Connected Components ← BFS or DFS
    105: [(102, 0.88), (103, 0.92)],  # Cycle Detection ← BFS or DFS
    106: [(103, 0.95), (104, 0.80)],  # Topo Sort ← DFS (critical)
    107: [(102, 0.95)],  # SCC ← BFS (Kosaraju or Tarjan)
    108: [(102, 0.88), (103, 0.88)],  # Bipartite ← BFS or DFS
    109: [(107, 0.95)],  # 2-SAT ← SCC (reduction)
    110: [(108, 0.92), (1703, 0.90)],  # Graph Matching ← Bipartite + Matching

    # Shortest path variants
    201: [(101, 0.80), (1004, 0.8)],  # Dijkstra ← Graphs + Priority Queue
    202: [(101, 0.80), (401, 0.65)],  # Bellman-Ford ← Graphs + DP thinking
    203: [(4, 0.90), (1, 0.80)],  # Floyd-Warshall ← DP (all-pairs)
    204: [(102, 0.95), (1003, 0.92)],  # 0-1 BFS ← BFS + Deque
    205: [(106, 0.95)],  # Shortest Path in DAG ← Topo Sort (DAG property)

    # Tree concepts
    301: [(103, 0.95)],  # Tree DFS ← DFS (trees are special graphs)
    302: [(4, 0.95), (301, 0.95)],  # Tree DP ← DP + Tree DFS
    303: [(301, 0.95)],  # LCA ← Tree DFS (basic tree traversal)
    304: [(301, 0.95), (1009, 0.85)],  # Binary Lifting ← Tree DFS + Sparse Table
    305: [(301, 0.95)],  # Tree Diameter ← Tree DFS (tree property)

    # DP variants - VERY CLOSELY RELATED
    401: [(10, 0.90), (1803, 0.85)],  # 1D DP ← DS + Recursion
    402: [(401, 0.95)],  # 2D DP ← 1D DP (natural extension)
    403: [(402, 0.95)],  # Knapsack ← 2D DP (classic 2D DP)
    404: [(401, 0.98)],  # LIS ← 1D DP (very similar structure)
    405: [(401, 0.98)],  # LCS ← 1D DP (very similar structure)
    406: [(405, 0.95), (402, 0.85)],  # Edit Distance ← LCS + 2D DP
    407: [(14, 0.98), (401, 0.92)],  # Bitmask DP ← Bitmasks + 1D DP (uses bitmask)
    408: [(401, 0.95)],  # Digit DP ← 1D DP (digit-based structure)
    409: [(4, 0.98), (301, 0.95)],  # Tree DP ← DP + Tree DFS (combines both)
    410: [(402, 0.95)],  # Interval DP ← 2D DP (interval-based)
    411: [(4, 0.98), (106, 0.90)],  # DP on DAG ← DP + Topo Sort

    # Greedy
    501: [(9, 0.90)],  # Activity Selection ← Sorting (needs sorting)
    502: [(9, 0.90)],  # Interval Scheduling ← Sorting (needs sorting)
    503: [(9, 0.95)],  # Greedy Sorting ← Sorting (IS sorting)

    # Binary Search - VERY CLOSELY RELATED
    601: [(9, 0.95)],  # Binary Search on Array ← Sorting (requires sorted)
    602: [(601, 0.95)],  # Binary Search on Answer ← Binary Search (variation)
    603: [(602, 0.95)],  # Ternary Search ← Binary Search on Answer (similar approach)

    # Two Pointers
    701: [(9, 0.85)],  # Sliding Window ← Sorting (often on sorted arrays)
    702: [(9, 0.98)],  # Two Pointers on Sorted Array ← Sorting (needs sorted)

    # Strings - CLOSELY RELATED
    801: [(10, 0.85)],  # String Matching ← DS (basic string ops)
    802: [(801, 0.98), (804, 0.95)],  # KMP ← String Matching + Prefix Func (KMP uses prefix)
    803: [(801, 0.95)],  # Z Algorithm ← String Matching (similar pattern matching)
    804: [(801, 0.95)],  # Prefix Function ← String Matching (used in KMP)
    805: [(801, 0.90)],  # Trie ← String Matching (string storage structure)
    806: [(801, 0.92)],  # Palindrome Detection ← String Matching (string property)
    807: [(1011, 0.95), (8, 0.90)],  # Hashing ← Hash Map + Strings (hash-based matching)

    # Sorting
    901: [(9, 0.95)],  # Custom Comparator ← Sorting (IS sorting)
    902: [(9, 0.90)],  # Coordinate Compression ← Sorting (uses sorted order)

    # Data Structures - INTERCONNECTED
    1002: [(1001, 0.95)],  # Queue ← Stack (both linear DS)
    1003: [(1002, 0.98), (1001, 0.95)],  # Deque ← Queue + Stack (combines both)
    1004: [(1001, 0.88), (1002, 0.88)],  # Priority Queue ← Stack/Queue (priority variant)
    1005: [(1001, 0.70), (1002, 0.70)],  # DSU ← Basic DS (union-find structure)
    1006: [(10, 0.95), (9, 0.80)],  # Fenwick Tree ← DS + Sorting (tree on array)
    1007: [(10, 0.95), (1803, 0.88)],  # Segment Tree ← DS + Recursion (recursive tree)
    1008: [(1007, 0.98)],  # Lazy Segment Tree ← Segment Tree (advanced variant)
    1009: [(10, 0.90)],  # Sparse Table ← DS (precomputed table)
    1010: [(10, 0.85)],  # Ordered Set ← DS (balanced set structure)
    1011: [(10, 0.85)],  # Hash Map ← DS (basic hash structure)
    1012: [(10, 0.85), (1011, 0.80)],  # Multiset ← DS + Hash Map (set variant)
    1013: [(1001, 0.98)],  # Monotonic Stack ← Stack (stack variant)
    1014: [(1002, 0.98), (1003, 0.92)],  # Monotonic Queue ← Queue + Deque (queue variant)
    1015: [(1007, 0.85), (701, 0.88)],  # Sqrt Decomposition ← Segment Tree + Sliding Window

    # Math - INTERCONNECTED
    1102: [(1101, 0.95)],  # LCM ← GCD (related via gcd)
    1103: [(1101, 0.90)],  # Modular Arithmetic ← GCD (number properties)
    1104: [(1103, 0.98)],  # Modular Inverse ← Modular Arithmetic (extension)
    1105: [(11, 0.85)],  # Fast Exponentiation ← Math (exponentiation)
    1106: [(1202, 0.95), (1101, 0.90)],  # Divisors ← Prime Factorization + GCD
    1107: [(1001, 0.90)],  # Difference Array ← Stack (array technique)
    1110: [(1103, 0.92)],  # Complex Numbers ← Modular Arithmetic (number system)
    1111: [(1103, 0.88), (401, 0.75)],  # Matrices ← Modular Arithmetic + DP

    # Number Theory
    1201: [(11, 0.90)],  # Prime Sieve ← Math (prime computation)
    1202: [(1201, 0.95)],  # Prime Factorization ← Prime Sieve (uses primes)
    1203: [(1103, 0.98), (1104, 0.92)],  # CRT ← Modular Arithmetic + Inverse

    # Combinatorics - CLOSELY RELATED
    1301: [(11, 0.85)],  # Permutations ← Math (counting)
    1302: [(11, 0.85)],  # Combinations ← Math (counting)
    1303: [(1302, 0.95)],  # Pascal Triangle ← Combinations (binomial coeffs)
    1304: [(1301, 0.90), (1302, 0.90)],  # Inclusion-Exclusion ← Permutations/Combinations
    1305: [(1302, 0.98), (1103, 0.92), (1104, 0.85)],  # Modular Combinations ← Combinations + Modular

    # Bitmasks
    1401: [(11, 0.90)],  # Bitmask Enumeration ← Math (bit operations)
    1402: [(1401, 0.98)],  # Submask Enumeration ← Bitmask Enumeration (variant)

    # Geometry
    1501: [(11, 0.80)],  # Distance ← Math (coordinate geometry)
    1502: [(1501, 0.95)],  # Orientation Test ← Distance (point relations)
    1503: [(1502, 0.95), (1501, 0.88)],  # Line Intersection ← Orientation + Distance
    1504: [(1501, 0.88)],  # Polygon Area ← Distance (geometry property)
    1505: [(1502, 0.98), (1501, 0.92), (9, 0.95)],  # Convex Hull ← Orientation + Sorting
    1506: [(1505, 0.98)],  # Rotating Calipers ← Convex Hull (convex property)
    1507: [(9, 0.92), (902, 0.85)],  # Sweep Line ← Sorting + Coord Compression

    # Probability
    1601: [(13, 0.92)],  # Expected Value ← Combinatorics (counting outcomes)
    1602: [(1601, 0.95), (13, 0.85)],  # Conditional Probability ← Expected Value

    # Flows
    1701: [(1, 0.98), (1004, 0.92)],  # Max Flow ← Graphs + Priority Queue (graph algorithm)
    1702: [(1701, 0.98)],  # Min Cut ← Max Flow (duality)
    1703: [(1701, 0.95), (108, 0.98)],  # Bipartite Matching ← Max Flow + Bipartite
    1704: [(1701, 0.98)],  # Min Cost Max Flow ← Max Flow (variant)

    # Implementation
    1801: [(10, 0.75)],  # Simulation ← DS (uses data structures)
    1802: [(10, 0.70)],  # Brute Force ← DS (might use DS)
    1803: [(10, 0.85)],  # Recursion ← DS (builds recursive structures)
    1804: [(1803, 0.98)],  # Backtracking ← Recursion (recursive search)
    1805: [(1803, 0.95)],  # State Simulation ← Recursion (state exploration)
    1806: [(1001, 0.92)],  # Prefix Sum ← Stack (array preprocessing)

    # String Suffix - CLOSELY RELATED
    1901: [(801, 0.98), (9, 0.92)],  # Suffix Array ← String Matching + Sorting
    1902: [(801, 0.98), (803, 0.92)],  # Suffix Automaton ← String Matching + Z Algorithm

    # Advanced Queries
    2001: [(1015, 0.98), (701, 0.95), (9, 0.92)],  # Mo's ← Sqrt Decomp + Sliding Window

    # ============ DIVIDE AND CONQUER ============
    2102: [(4, 0.88), (24,0.95)],  # Meet-in-the-middle ← DP (combines results)+ brute force
    2101: [(4, 0.80)],  # FFT ← DP thinking (complex optimization)

    # ============ CONSTRUCTIVE ============
    2201: [(18, 0.90)],  # Constructive Techniques ← Implementation (building solutions)
    2202: [(501, 0.92), (502, 0.92)],  # Schedules ← Activity/Interval Selection
    2203: [(801, 0.95), (1001, 0.85)],  # Expression Parsing ← Strings + Stack (parse)
    2204: [(1801, 0.92)],  # Interactive ← Simulation (interactive strategy)

    # ============ GAME THEORY ============
    2301: [(13, 0.92), (11, 0.85)],  # Game Theory ← Combinatorics + Math
}



rows = []

# add parent KCs
for cid, name in parents.items():
    rows.append((name, cid))

# add child KCs
for parent_id, child_list in children.items():
    for entity_id, kc_name, _level in child_list:
        rows.append((kc_name, entity_id))

# sort by entity_id for cleanliness (optional but nice)
rows.sort(key=lambda x: x[1])

# write CSV
with open("kc_vocab.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["kc_name", "entity_id"])
    writer.writerows(rows)

print("kc_vocab.csv created!")

# import json
# from embeddings.KnowledgeGraph import KnowledgeGraph
# def build_kc_graph(kgraph):
#     edges = []

#     # ONLY prerequisites (important!)
#     for to_id, prereqs in kgraph.prerequisites.items():
#         to_name = kgraph.all_concepts[to_id]["name"]

#         for from_id, weight in prereqs:
#             if from_id in kgraph.all_concepts:
#                 from_name = kgraph.all_concepts[from_id]["name"]

#                 edges.append({
#                     "from_kc": from_name,
#                     "to_kc": to_name,
#                     "weight": weight
#                 })

#     return edges


# kg = KnowledgeGraph()
# graph = build_kc_graph(kg)

# with open("kc_graph.json", "w", encoding="utf-8") as f:
#     json.dump(graph, f, indent=2)

# print("kc_graph.json created!")