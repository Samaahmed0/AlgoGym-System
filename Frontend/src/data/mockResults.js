export const mockSuccessResult = {
  verdict: "ACCEPTED",
  passedTests: 3,
  totalTests: 3,
  executionTimeMs: 45,
  memoryUsedKb: 12800,
  output: "[0, 1]\n[1, 2]\n[0, 3]",
  testResults: [
    { testNumber: 1, passed: true, input: "[2,7,11,15], 9", expectedOutput: "[0,1]", actualOutput: "[0,1]" },
    { testNumber: 2, passed: true, input: "[3,2,4], 6", expectedOutput: "[1,2]", actualOutput: "[1,2]" },
    { testNumber: 3, passed: true, input: "[3,3], 6", expectedOutput: "[0,1]", actualOutput: "[0,1]" }
  ]
};

export const mockWrongAnswerResult = {
  verdict: "WRONG_ANSWER",
  passedTests: 2,
  totalTests: 3,
  executionTimeMs: 38,
  memoryUsedKb: 11200,
  firstFailedInput: "[3,2,4], 6",
  firstFailedExpected: "[1,2]",
  firstFailedActual: "[0,1]",
  output: "[0, 1]\n[1, 2]\n[0, 1]",
  testResults: [
    { testNumber: 1, passed: true, input: "[2,7,11,15], 9", expectedOutput: "[0,1]", actualOutput: "[0,1]" },
    { testNumber: 2, passed: true, input: "[3,3], 6", expectedOutput: "[0,1]", actualOutput: "[0,1]" },
    { testNumber: 3, passed: false, input: "[3,2,4], 6", expectedOutput: "[1,2]", actualOutput: "[0,1]" }
  ],
  aiCoach: {
    errorType: "LOGIC_ERROR",
    explanation: "It seems like you're returning the indices based on a 0-indexed array, but the problem might expect 1-indexed or specific sorting. Also, check edge cases where the target might be negative.",
    tips: [
      "Try using a hash map to store complements as you iterate through the array. This reduces complexity from O(n²) to O(n).",
      "Make sure you're not using the same element twice - check if i != j before returning.",
      "Test with negative numbers and duplicate values."
    ]
  }
};

export const mockCompilationError = {
  verdict: "COMPILATION_ERROR",
  passedTests: 0,
  totalTests: 3,
  compilationError: "SyntaxError: Unexpected token '}' at line 5:12",
  aiCoach: {
    errorType: "SYNTAX_ERROR",
    explanation: "You have a syntax error in your code. There's an extra closing brace '}' that doesn't match any opening brace.",
    tips: [
      "Check line 5 - you might have an extra closing brace or missing an opening one.",
      "Make sure all your parentheses, brackets, and braces are properly paired.",
      "Try using an IDE with syntax highlighting to catch these errors early."
    ]
  }
};

export const mockRuntimeError = {
  verdict: "RUNTIME_ERROR",
  passedTests: 1,
  totalTests: 3,
  executionTimeMs: 12,
  memoryUsedKb: 8400,
  runtimeError: "IndexError: list index out of range at line 8",
  firstFailedInput: "[2], 4",
  output: "[0,1]\nError\nError",
  testResults: [
    { testNumber: 1, passed: true, input: "[2,7,11,15], 9", expectedOutput: "[0,1]", actualOutput: "[0,1]" },
    { testNumber: 2, passed: false, input: "[2], 4", error: "IndexError: list index out of range" },
    { testNumber: 3, passed: false, input: "[], 0", error: "IndexError: list index out of range" }
  ],
  aiCoach: {
    errorType: "RUNTIME_ERROR",
    explanation: "Your code is trying to access an array index that doesn't exist. This typically happens when the array is too small or empty.",
    tips: [
      "Add a check to ensure the array has at least 2 elements before proceeding.",
      "Test edge cases: empty arrays, single-element arrays, and arrays with duplicate values.",
      "Use array.length checks before accessing indices."
    ]
  }
};