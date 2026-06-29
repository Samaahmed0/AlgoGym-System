export const recommendedByWeakness = [
  {
    id: "dp",
    name: "Dynamic Programming",
    accuracy: 45,
    accent: "#a855f7",
    glow: "rgba(168, 85, 247, 0.18)",
    topicHints: ["dp", "dynamic"],
    insight: "Gaps in state transitions and memoization — start here.",
    recommendations: [
      {
        title: "Mini Metro",
        difficulty: "Hard",
        topic: "DP",
        reason: "Builds bottom-up thinking with overlapping subproblems.",
      },
      {
        title: "Homework",
        difficulty: "Medium",
        topic: "Greedy",
        reason: "A stepping stone before heavier DP patterns.",
      },
    ],
  },
  {
    id: "graphs",
    name: "Graph Theory",
    accuracy: 52,
    accent: "#6366f1",
    glow: "rgba(99, 102, 241, 0.18)",
    topicHints: ["graph", "bfs", "dfs", "tree"],
    insight: "Traversal and shortest-path need more consistency.",
    recommendations: [
      {
        title: "Course Schedule",
        difficulty: "Medium",
        topic: "Graphs",
        reason: "Topological sort to strengthen dependency reasoning.",
      },
      {
        title: "Word Ladder",
        difficulty: "Hard",
        topic: "Graphs",
        reason: "BFS shortest-path on an implicit graph.",
      },
    ],
  },
  {
    id: "bit",
    name: "Bit Manipulation",
    accuracy: 58,
    accent: "#d946ef",
    glow: "rgba(217, 70, 239, 0.18)",
    topicHints: ["bit", "xor", "mask"],
    insight: "Bitwise tricks show up often in missed submissions.",
    recommendations: [
      {
        title: "Single Number",
        difficulty: "Easy",
        topic: "Bit Manipulation",
        reason: "Gentle intro to XOR before harder bitmask patterns.",
      },
      {
        title: "Valid Parentheses",
        difficulty: "Easy",
        topic: "Stacks",
        reason: "Light warm-up while building bit-manipulation fluency.",
      },
    ],
  },
];

/** Shown only in the "See more" weak areas popup */
export const additionalWeakAreas = [
  {
    id: "arrays",
    name: "Arrays & Hashing",
    accuracy: 61,
    accent: "#10b981",
    insight: "Frequency maps and two-pointer patterns need sharpening.",
  },
  {
    id: "trees",
    name: "Trees & BST",
    accuracy: 63,
    accent: "#3b82f6",
    insight: "Recursive traversal and parent-child logic could be stronger.",
  },
  {
    id: "greedy",
    name: "Greedy Algorithms",
    accuracy: 67,
    accent: "#f59e0b",
    insight: "Local optimal choices are sometimes missed on harder sets.",
  },
  {
    id: "sorting",
    name: "Sorting & Searching",
    accuracy: 71,
    accent: "#0ea5e9",
    insight: "Custom comparators and binary search bounds need review.",
  },
];

export const recommendedSummary = {
  totalPicks: recommendedByWeakness.reduce((n, w) => n + w.recommendations.length, 0),
  weakAreas: recommendedByWeakness.length,
  lastUpdated: "Today",
};
