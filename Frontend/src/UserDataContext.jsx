import React, { createContext, useContext, useRef, useState, useCallback } from "react";
import { fetchStudentDashboard } from "./api/studentDashboard.api";
import { fetchProblems, fetchProblemTags } from "./api/problems.api";
import { fetchProgress } from "./api/progress.api";
import { fetchRecommendations } from "./api/recommendations.api";
import { fetchCurrentUser } from "./api/user.api";

const UserDataContext = createContext(null);

function problemsCacheKey(page, size, title, difficulty, topic, status) {
  return `${page}|${size}|${title}|${difficulty.join(",")}|${topic.join(",")}|${status.join(",")}`;
}

export function UserDataProvider({ children }) {
  const dashboardCache = useRef(null);
  const problemsCache = useRef(new Map());
  const problemTagsCache = useRef(null);
  const progressCache = useRef(null);
  const recommendationsCache = useRef(null);
  const profileCache = useRef(null);

  const [dashboardVersion, setDashboardVersion] = useState(0);
  const [problemsVersion, setProblemsVersion] = useState(0);
  const [progressVersion, setProgressVersion] = useState(0);
  const [recommendationsVersion, setRecommendationsVersion] = useState(0);
  const [profileVersion, setProfileVersion] = useState(0);

  const getDashboard = useCallback(async () => {
    if (dashboardCache.current) return dashboardCache.current;
    const data = await fetchStudentDashboard();
    dashboardCache.current = data;
    return data;
  }, []);

  const invalidateDashboard = useCallback(() => {
    dashboardCache.current = null;
    setDashboardVersion(v => v + 1);
  }, []);

  const recordSubmissionActivity = useCallback(async (submission, problem, languageName) => {
    const formatRuntime = (ms) =>
      ms != null ? `${Math.round(ms)}ms` : "N/A";
    const formatMemory = (kb) =>
      kb != null ? `${(kb / 1024).toFixed(1)}MB` : "N/A";
    const resolveDifficulty = (p) => {
      if (p?.difficulty) return String(p.difficulty).toUpperCase();
      const rating = p?.rating;
      if (rating == null) return "MEDIUM";
      if (rating < 1200) return "EASY";
      if (rating < 1600) return "MEDIUM";
      return "HARD";
    };

    const activityItem = {
      problemId: problem.id,
      submissionId: submission.submissionId,
      problemTitle: problem.title,
      difficulty: resolveDifficulty(problem),
      verdict: submission.verdict,
      submittedAt: submission.submittedAt ?? new Date().toISOString(),
      tag: problem.tags?.[0] ?? "",
      runtime: formatRuntime(submission.executionTimeMs),
      memory: formatMemory(submission.memoryUsedKb),
      language: languageName ?? "N/A",
      testsPassed: submission.passedTests ?? "N/A",
      totalTests: submission.totalTests ?? "N/A",
    };

    const base = dashboardCache.current ?? {
      stats: {},
      performanceData: [],
      recentActivity: { activities: [] },
    };

    dashboardCache.current = {
      ...base,
      recentActivity: {
        ...base.recentActivity,
        activities: [activityItem, ...(base.recentActivity?.activities ?? [])],
      },
    };
    setDashboardVersion((v) => v + 1);

    try {
      const fresh = await fetchStudentDashboard();
      dashboardCache.current = fresh;
      setDashboardVersion((v) => v + 1);
    } catch {
      // Keep optimistic activity if the refresh fails.
    }
  }, []);

  const getProblems = useCallback(async (page, size, filters) => {
    const key = problemsCacheKey(
      page,
      size,
      filters.title ?? "",
      filters.difficulty ?? [],
      filters.topic ?? [],
      filters.status ?? []
    );
    if (problemsCache.current.has(key)) return problemsCache.current.get(key);
    const data = await fetchProblems({
      page,
      size,
      title: filters.title,
      difficulty: filters.difficulty,
      topic: filters.topic,
      status: filters.status,
    });
    problemsCache.current.set(key, data);
    return data;
  }, []);

  const getProblemTags = useCallback(async () => {
    if (problemTagsCache.current) return problemTagsCache.current;
    const data = await fetchProblemTags();
    problemTagsCache.current = data;
    return data;
  }, []);

  const invalidateProblems = useCallback(() => {
    problemsCache.current.clear();
    problemTagsCache.current = null;
    setProblemsVersion(v => v + 1);
  }, []);

  const getProgress = useCallback(async () => {
    if (progressCache.current) return progressCache.current;
    const data = await fetchProgress();
    progressCache.current = data;
    return data;
  }, []);

  const invalidateProgress = useCallback(() => {
    progressCache.current = null;
    setProgressVersion(v => v + 1);
  }, []);

  const getRecommendations = useCallback(async () => {
    if (recommendationsCache.current) return recommendationsCache.current;
    const data = await fetchRecommendations();
    recommendationsCache.current = data;
    return data;
  }, []);

  const invalidateRecommendations = useCallback(() => {
    recommendationsCache.current = null;
    setRecommendationsVersion(v => v + 1);
  }, []);

  const getProfile = useCallback(async () => {
    if (profileCache.current) return profileCache.current;
    const data = await fetchCurrentUser();
    profileCache.current = data;
    return data;
  }, []);

  const invalidateProfile = useCallback(() => {
    profileCache.current = null;
    setProfileVersion(v => v + 1);
  }, []);

  return (
    <UserDataContext.Provider
      value={{
        getDashboard, invalidateDashboard, recordSubmissionActivity, dashboardVersion,
        getProblems, getProblemTags, invalidateProblems, problemsVersion,
        getProgress, invalidateProgress, progressVersion,
        getRecommendations, invalidateRecommendations, recommendationsVersion,
        getProfile, invalidateProfile, profileVersion,
      }}
    >
      {children}
    </UserDataContext.Provider>
  );
}

export function useUserData() {
  const ctx = useContext(UserDataContext);
  if (!ctx) throw new Error("useUserData must be used inside UserDataProvider");
  return ctx;
}
