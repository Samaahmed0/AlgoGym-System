import React, { createContext, useContext, useRef, useState, useCallback } from "react";
import {
  fetchAdminUsers, fetchAdminProblems, fetchAdminSubmissions,
  fetchAnalyticsOverview, fetchTopHardestProblems, fetchTopEasiestProblems, fetchMostActiveUsers, fetchAllTags, fetchMostAttemptedTags,
  fetchAIFeedbackStats, fetchBroadcastNotifications, fetchAdminSettings,
  fetchAdminStats, fetchAdminHealth,
} from "../api/admin.api";

const AdminDataContext = createContext(null);

export function AdminDataProvider({ children }) {
  const usersCache = useRef(new Map());
  const problemsCache = useRef(new Map());
  const submissionsCache = useRef(new Map());
  const analyticsCache = useRef(new Map());
  const tagsCache = useRef(new Map());
  const aiFeedbackCache = useRef(null);
  const broadcastsCache = useRef(null);
  const settingsCache = useRef(null);
  const [overviewStats, setOverviewStats] = useState(null);
  const [overviewHealth, setOverviewHealth] = useState(null);
  const [analyticsByDays, setAnalyticsByDays] = useState({});

  const [usersVersion, setUsersVersion] = useState(0);
  const [problemsVersion, setProblemsVersion] = useState(0);
  const [submissionsVersion, setSubmissionsVersion] = useState(0);
  const [tagsVersion, setTagsVersion] = useState(0);
  const [aiFeedbackVersion, setAiFeedbackVersion] = useState(0);
  const [broadcastsVersion, setBroadcastsVersion] = useState(0);
  const [settingsVersion, setSettingsVersion] = useState(0);

  const getUsers = useCallback(async (page, size, search) => {
    const key = `${page}|${size}|${search}`;
    if (usersCache.current.has(key)) return usersCache.current.get(key);
    const data = await fetchAdminUsers(page, size, search);
    usersCache.current.set(key, data);
    return data;
  }, []);

  const invalidateUsers = useCallback(() => {
    usersCache.current.clear();
    setUsersVersion(v => v + 1);
  }, []);

  const getProblems = useCallback(async (page, size, search, difficulty, visible) => {
    const key = `${page}|${size}|${search}|${difficulty}|${visible}`;
    if (problemsCache.current.has(key)) return problemsCache.current.get(key);
    const data = await fetchAdminProblems(page, size, search, difficulty, visible);
    problemsCache.current.set(key, data);
    return data;
  }, []);

  const invalidateProblems = useCallback(() => {
    problemsCache.current.clear();
    setProblemsVersion(v => v + 1);
  }, []);

  const getSubmissions = useCallback(async (page, size, filters) => {
    const key = `${page}|${size}|${filters.verdict}|${filters.language}|${filters.userId}|${filters.problemId}`;
    if (submissionsCache.current.has(key)) return submissionsCache.current.get(key);
    const data = await fetchAdminSubmissions(page, size, filters);
    submissionsCache.current.set(key, data);
    return data;
  }, []);

  const invalidateSubmissions = useCallback(() => {
    submissionsCache.current.clear();
    setSubmissionsVersion(v => v + 1);
  }, []);

  const getOverviewStats = useCallback(async () => {
    if (overviewStats) return overviewStats;
    const data = await fetchAdminStats();
    setOverviewStats(data);
    return data;
  }, [overviewStats]);

  const getOverviewHealth = useCallback(async () => {
    if (overviewHealth) return overviewHealth;
    const data = await fetchAdminHealth();
    setOverviewHealth(data);
    return data;
  }, [overviewHealth]);

  const refreshOverviewStats = useCallback(async () => {
    const data = await fetchAdminStats();
    setOverviewStats(data);
    return data;
  }, []);

  const refreshOverviewHealth = useCallback(async () => {
    const data = await fetchAdminHealth();
    setOverviewHealth(data);
    return data;
  }, []);

  const invalidateOverview = useCallback(() => {
    setOverviewStats(null);
    setOverviewHealth(null);
  }, []);

  const getCachedAnalytics = useCallback(
    (days) => analyticsByDays[days] ?? null,
    [analyticsByDays]
  );

  const getAnalytics = useCallback(async (days) => {
    if (analyticsByDays[days]) return analyticsByDays[days];

    const rankingsKey = `rankings|${days}`;
    let hardest;
    let easiest;
    let mostActive;

    if (analyticsCache.current.has(rankingsKey)) {
      ({ hardest, easiest, mostActive } = analyticsCache.current.get(rankingsKey));
    } else {
      [hardest, easiest, mostActive] = await Promise.all([
        fetchTopHardestProblems(10),
        fetchTopEasiestProblems(10),
        fetchMostActiveUsers(10),
      ]);
      analyticsCache.current.set(rankingsKey, { hardest, easiest, mostActive });
    }

    const overview = await fetchAnalyticsOverview(days);
    const data = { overview, hardest, easiest, mostActive };
    setAnalyticsByDays(prev => ({ ...prev, [days]: data }));
    return data;
  }, [analyticsByDays]);

  const invalidateAnalytics = useCallback(() => {
    analyticsCache.current.clear();
    setAnalyticsByDays({});
  }, []);

  const getTags = useCallback(async (mode) => {
    const key = `tags|${mode}`;
    if (tagsCache.current.has(key)) return tagsCache.current.get(key);
    const data = mode === "most-attempted" ? await fetchMostAttemptedTags() : await fetchAllTags();
    tagsCache.current.set(key, data);
    return data;
  }, []);

  const invalidateTags = useCallback(() => {
    tagsCache.current.clear();
    setTagsVersion(v => v + 1);
  }, []);

  const getAIFeedbackStats = useCallback(async () => {
    if (aiFeedbackCache.current) return aiFeedbackCache.current;
    const data = await fetchAIFeedbackStats();
    aiFeedbackCache.current = data;
    return data;
  }, []);

  const invalidateAIFeedback = useCallback(() => {
    aiFeedbackCache.current = null;
    setAiFeedbackVersion(v => v + 1);
  }, []);

  const getBroadcastNotifications = useCallback(async () => {
    if (broadcastsCache.current) return broadcastsCache.current;
    const data = await fetchBroadcastNotifications();
    broadcastsCache.current = data;
    return data;
  }, []);

  const invalidateBroadcasts = useCallback(() => {
    broadcastsCache.current = null;
    setBroadcastsVersion(v => v + 1);
  }, []);

  const getSettings = useCallback(async () => {
    if (settingsCache.current) return settingsCache.current;
    const data = await fetchAdminSettings();
    settingsCache.current = data;
    return data;
  }, []);

  const invalidateSettings = useCallback(() => {
    settingsCache.current = null;
    setSettingsVersion(v => v + 1);
  }, []);

  return (
    <AdminDataContext.Provider
      value={{
        getUsers, invalidateUsers, usersVersion,
        getProblems, invalidateProblems, problemsVersion,
        getSubmissions, invalidateSubmissions, submissionsVersion,
        overviewStats, overviewHealth,
        getOverviewStats, getOverviewHealth, refreshOverviewStats, refreshOverviewHealth, invalidateOverview,
        getAnalytics, getCachedAnalytics, invalidateAnalytics,
        getTags, invalidateTags, tagsVersion,
        getAIFeedbackStats, invalidateAIFeedback, aiFeedbackVersion,
        getBroadcastNotifications, invalidateBroadcasts, broadcastsVersion,
        getSettings, invalidateSettings, settingsVersion,
      }}
    >
      {children}
    </AdminDataContext.Provider>
  );
}

export function useAdminData() {
  const ctx = useContext(AdminDataContext);
  if (!ctx) throw new Error("useAdminData must be used inside AdminDataProvider");
  return ctx;
}