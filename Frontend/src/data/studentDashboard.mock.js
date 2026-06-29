export const studentDashboardMock = {
  student: {
    id: "stu_123",
    name: "Alex"
  },

  stats: {
    solved: 142,
    rank: 1284,
    rating: 1650,
    streak: 12
  },

  focusAreas: [
    { id: 1, name: "Dynamic Programming", accuracy: 45 },
    { id: 2, name: "Graph Theory", accuracy: 52 },
    { id: 3, name: "Bit Manipulation", accuracy: 58 }
  ],
 
  
  recommendations: [
    { id: 1, title: "Dijkstra's Algorithm", topic: "Graphs", difficulty: "Hard", points: 150 },
    { id: 2, title: "Longest Palindromic Substring", topic: "DP", difficulty: "Medium", points: 100 },
    { id: 3, title: "Valid Parentheses", topic: "Stacks", difficulty: "Easy", points: 50 },
  ]
,

  recentActivity: Array.from({ length: 28 }).map((_, i) => ({
    id: i + 1,
    title: `Solved Problem #${i + 1}`,
    topic: ["DP", "Graphs", "Arrays"][i % 3],
    difficulty: ["Easy", "Medium", "Hard"][i % 3],
    solvedAt: `2026-02-${(i % 28) + 1}`
  }))
};
//dummy data
