package com.AlgoGym.backend.service;

import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.TestCase;
import com.AlgoGym.backend.model.TestResult;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.service.UserProgressService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class CodeExecutionService {

    @Autowired
    private Judge0Service judge0Service;

    @Autowired
    private ProblemRepository problemRepository;

    @Autowired
    private SubmissionRepository submissionRepository;
    @Autowired
    private AIFeedbackService aiFeedbackService;
    @Autowired
    private AIFeedbackRepository aiFeedbackRepository;
    @Autowired
    private UserProgressService userProgressService;


    // all test cases and save
    public Submission executeCode(String userId, String problemId, String sourceCode, Integer languageId, String languageName) {
        Problem problem = problemRepository.findById(problemId)
                .orElseThrow(() -> new RuntimeException("Problem not found: " + problemId));

        List<TestCase> allTests = new ArrayList<>();
        if (problem.getExamples() != null) allTests.addAll(problem.getExamples());
        if (problem.getOfficialTests() != null) allTests.addAll(problem.getOfficialTests());

        return executeTestCases(userId, problemId, sourceCode, languageId, languageName, allTests, problem, true);
    }

    // example test cases only, don't save
    public Submission runCode(String userId, String problemId, String sourceCode, Integer languageId, String languageName) {
        Problem problem = problemRepository.findById(problemId)
                .orElseThrow(() -> new RuntimeException("Problem not found: " + problemId));

        List<TestCase> exampleTests = new ArrayList<>();
        if (problem.getExamples() != null) exampleTests.addAll(problem.getExamples());

        if (exampleTests.isEmpty()) {
            throw new RuntimeException("No example test cases found for this problem");
        }

        return executeTestCases(userId, problemId, sourceCode, languageId, languageName, exampleTests, problem, false);
    }


    private TestResult parseTestResult(int testNumber, TestCase testCase, Map<String, Object> judge0Result, Double timeLimit, Double memoryLimit) {
        TestResult result = new TestResult();
        result.setTestNumber(testNumber);
        result.setInput(testCase.getInput());
        result.setExpectedOutput(testCase.getOutput());

        Map<String, Object> status = (Map<String, Object>) judge0Result.get("status");
        Integer statusId = (Integer) status.get("id");

//        String stdout = (String) judge0Result.get("stdout");
        String stdout = decode(judge0Result.get("stdout"));
        String timeStr = (String) judge0Result.get("time");
        Integer memory = (Integer) judge0Result.get("memory");

        Double executionTime = null;
        if (timeStr != null) {
            try {
                executionTime = Double.parseDouble(timeStr) * 1000;
            } catch (NumberFormatException ignored) {
            }
        }

        result.setExecutionTime(executionTime);
        result.setMemoryUsed(memory != null ? memory.doubleValue() : null);

        // Memory limit check
        if (memory != null && memoryLimit != null && memory > memoryLimit) {
            result.setPassed(false);
            result.setError("Memory Limit Exceeded: " + memory + " KB > " + memoryLimit.intValue() + " KB");
            return result;
        }

        // Time limit check
        if (executionTime != null && timeLimit != null) {
            double timeLimitMs = timeLimit * 1000;
            if (executionTime > timeLimitMs) {
                result.setPassed(false);
                result.setError("Time Limit Exceeded: " +
                        String.format("%.2f", executionTime) + " ms > " +
                        String.format("%.2f", timeLimitMs) + " ms");
                return result;
            }
        }

        String actualOutput = stdout != null ? stdout.trim().replace("\r\n", "\n").replace("\r", "\n") : "";
        String expectedOutput = testCase.getOutput().trim().replace("\r\n", "\n").replace("\r", "\n");
        boolean passed = (statusId == 3) && actualOutput.equals(expectedOutput);

        result.setPassed(passed);
        result.setActualOutput(actualOutput);

        if (!passed && statusId == 3) {
            result.setError("Wrong Answer");
        }

        return result;
    }

    private Submission executeTestCases(String userId, String problemId, String sourceCode, Integer languageId, String languageName, List<TestCase> testCases, Problem problem, boolean saveToDatabase) {
        List<TestResult> testResults = new ArrayList<>();
        int passedTests = 0;

        String firstFailedInput = null;
        String firstFailedExpected = null;
        String firstFailedActual = null;

        String compilationError = null;
        String runtimeError = null;
        boolean timeLimitExceeded = false;
        boolean memoryLimitExceeded = false;

        double totalTime = 0.0;
        double totalMemory = 0.0;

        Double memoryLimitKb = problem.getMemoryLimit() != null ? problem.getMemoryLimit() * 1024.0 : null;

        for (int i = 0; i < testCases.size(); i++) {
            TestCase testCase = testCases.get(i);

            try {
                String token = judge0Service.submitCode(
                        sourceCode,
                        languageId,
                        testCase.getInput(),
                        getAdjustedTimeLimit(problem.getTimeLimit(), languageId),
                        memoryLimitKb
                );

                Map<String, Object> result = judge0Service.waitForResult(token);
                Map<String, Object> status = (Map<String, Object>) result.get("status");
                Integer statusId = (Integer) status.get("id");

//                String stdout       = (String) result.get("stdout");
//                String stderr       = (String) result.get("stderr");
//                String compileOutput = (String) result.get("compile_output");
                String stdout = decode(result.get("stdout"));
                String stderr = decode(result.get("stderr"));
                String compileOutput = decode(result.get("compile_output"));

                System.out.println("=== Judge0 Test " + (i + 1) + " === statusId=" + statusId + " desc=" + status.get("description"));
                System.out.println("  stdout=[" + result.get("stdout") + "]");
                System.out.println("  stderr=[" + result.get("stderr") + "]");
                System.out.println("  compile_output=[" + result.get("compile_output") + "]");

                // ── 1. COMPILATION ERROR ──────────────────────────────────────
                boolean hasCompileOutput = compileOutput != null && !compileOutput.isBlank();
                if (statusId == 6 || hasCompileOutput) {
                    compilationError = "";
                    if (hasCompileOutput) compilationError += compileOutput.trim();
                    if (stderr != null && !stderr.isBlank()) {
                        if (!compilationError.isEmpty()) compilationError += "\n";
                        compilationError += stderr.trim();
                    }

                    break;
                }

                // ── 2. TIME LIMIT EXCEEDED ────────────────────────────────────
                if (statusId == 5) {
                    timeLimitExceeded = true;
                    firstFailedInput = testCase.getInput();
                    firstFailedExpected = testCase.getOutput();
                    break;
                }

                // ── 3. RUNTIME ERROR ──────────────────────────────────────────
                // Status 11 = Runtime Error (NZEC)
                // Status 12 = Runtime Error (SIGSEGV - segfault / out of bounds)
                // Status 13 = Runtime Error (SIGXFSZ)
                // Status 14 = Runtime Error (SIGFPE - division by zero)
                // Status 15 = Runtime Error (SIGABRT)
                // Status 7  = Runtime Error (generic)
                boolean isRuntimeError = (statusId == 7) || (statusId >= 11 && statusId <= 15);
                boolean silentCrash = (statusId == 3)
                        && (stdout == null || stdout.isBlank())
                        && (stderr != null && !stderr.isBlank());

                if (isRuntimeError || silentCrash) {
                    String statusDesc = (String) status.get("description");
                    String errorDetails = "";
                    if (statusDesc != null && !statusDesc.isBlank()) {
                        errorDetails += statusDesc.trim();
                    }
                    if (stderr != null && !stderr.isBlank()) {
                        if (!errorDetails.isEmpty()) errorDetails += "\n";
                        errorDetails += stderr.trim();
                    }
                    if (errorDetails.isEmpty()) errorDetails = "Runtime error occurred.";

                    // ── Python/interpreted language syntax errors come back as NZEC ──
                    // Detect SyntaxError, IndentationError, NameError etc. in stderr
                    // and reclassify as compilation error so user sees the right verdict
                    boolean isSyntaxError = stderr != null && (
                            stderr.contains("SyntaxError") ||
                                    stderr.contains("IndentationError") ||
                                    stderr.contains("TabError")
                    );

                    if (isSyntaxError) {
                        // Treat as compilation error — input is irrelevant
                        compilationError = errorDetails;
                    } else {
                        runtimeError = errorDetails;
                        firstFailedInput = testCase.getInput();
                        firstFailedExpected = testCase.getOutput();
                    }
                    break;
                }

                // ── 4. WRONG ANSWER / ACCEPTED ───────────────────────────────
                TestResult testResult = parseTestResult(
                        i + 1, testCase, result, problem.getTimeLimit(), memoryLimitKb
                );
                testResults.add(testResult);

                if (!testResult.getPassed() && testResult.getError() != null
                        && testResult.getError().contains("Memory Limit Exceeded")) {
                    memoryLimitExceeded = true;
                    firstFailedInput = testCase.getInput();
                    firstFailedExpected = testCase.getOutput();
                    break;
                }

                if (testResult.getPassed()) {
                    passedTests++;
                    if (testResult.getExecutionTime() != null) totalTime += testResult.getExecutionTime();
                    if (testResult.getMemoryUsed() != null) totalMemory += testResult.getMemoryUsed();
                } else {
                    if (firstFailedInput == null) {
                        firstFailedInput = testCase.getInput();
                        firstFailedExpected = testCase.getOutput();
                        firstFailedActual = testResult.getActualOutput();
                    }
                    break;
                }

            } catch (Exception e) {
                TestResult errorResult = new TestResult();
                errorResult.setTestNumber(i + 1);
                errorResult.setPassed(false);
                errorResult.setInput(testCase.getInput());
                errorResult.setExpectedOutput(testCase.getOutput());
                errorResult.setError("System error: " + e.getMessage());
                testResults.add(errorResult);
                break;
            }
        }

        // ── VERDICT (order matters — compilation > TLE > MLE > RTE > WA > AC) ──
        String verdict;
        if (compilationError != null) verdict = "COMPILATION_ERROR";
        else if (timeLimitExceeded) verdict = "TIME_LIMIT_EXCEEDED";
        else if (memoryLimitExceeded) verdict = "MEMORY_LIMIT_EXCEEDED";
        else if (runtimeError != null) verdict = "RUNTIME_ERROR";
        else if (passedTests == testCases.size()) verdict = "ACCEPTED";
        else verdict = "WRONG_ANSWER";

        Double avgTime = passedTests > 0 ? totalTime / passedTests : null;
        Double avgMemory = passedTests > 0 ? totalMemory / passedTests : null;

        Submission submission = Submission.builder()
                .userId(userId)
                .problemId(problemId)
                .sourceCode(sourceCode)
                .languageId(languageId)
                .languageName(languageName)
                .verdict(verdict)
                .passedTests(passedTests)
                .totalTests(testCases.size())
                .testResults(testResults)
                .firstFailedInput(firstFailedInput)
                .firstFailedExpected(firstFailedExpected)
                .firstFailedActual(firstFailedActual)
                .compilationError(compilationError)
                .runtimeError(runtimeError)
                .timeLimitExceeded(timeLimitExceeded)
                .memoryLimitExceeded(memoryLimitExceeded)
                .executionTimeMs(avgTime)
                .memoryUsedKb(avgMemory)
                .submittedAt(LocalDateTime.now())
                .build();

        if (saveToDatabase) {
            Submission saved = submissionRepository.save(submission);
            userProgressService.updateProgress(saved);
            if (!"ACCEPTED".equals(saved.getVerdict())) {
                aiFeedbackService.generateAndSave(saved);
            }
            return saved;
        }else {
            return submission;
        }
    }

    private String decode(Object value) {
        if (value == null) return null;
        String str = value.toString().trim();
        if (str.isEmpty()) return null;
        try {
            byte[] decoded = java.util.Base64.getDecoder().decode(str);
            String result = new String(decoded, java.nio.charset.StandardCharsets.UTF_8).trim();
            System.out.println("  decode: [" + str + "] -> [" + result + "]");
            return result.isEmpty() ? null : result;
        } catch (Exception e) {
            System.out.println("  decode failed for [" + str + "]: " + e.getMessage());
            return str;
        }
    }

    private Double getAdjustedTimeLimit(Double baseLimit, Integer languageId) {
        if (baseLimit == null) return null;
        // Node.js needs more time due to startup overhead
        if (languageId == 63 || languageId == 93 || languageId == 97 || languageId == 102) {
            return baseLimit * 3;
        }
        // Java also has JVM startup overhead
        if (languageId == 62 || languageId == 91 || languageId == 96) {
            return baseLimit * 2;
        }
        return baseLimit;
    }

}