export const difficultyClass = (d) => d?.toLowerCase() ?? "medium";

function normalizeTitle(value) {
  return (value ?? "").trim().toLowerCase();
}

function matchesTopicHint(tags, hints) {
  const tagList = (tags ?? []).map((t) => t.toLowerCase());
  return hints.some((hint) =>
    tagList.some((tag) => tag.includes(hint) || hint.includes(tag))
  );
}

export function resolveRecommendations(areas, apiProblems) {
  const used = new Set();

  const takeProblem = (predicate) => {
    const match = apiProblems.find((p) => p?.id && !used.has(p.id) && predicate(p));
    if (match) used.add(match.id);
    return match ?? null;
  };

  return areas.map((area) => ({
    ...area,
    recommendations: area.recommendations.map((rec) => {
      const byTitle = takeProblem(
        (p) => normalizeTitle(p.title) === normalizeTitle(rec.title)
      );
      if (byTitle) {
        return {
          ...rec,
          resolvedId: byTitle.id,
          title: byTitle.title,
          difficulty: byTitle.difficulty ?? rec.difficulty,
          topic: rec.topic,
        };
      }

      const byTopic = takeProblem((p) => matchesTopicHint(p.tags, area.topicHints));
      if (byTopic) {
        return {
          ...rec,
          resolvedId: byTopic.id,
          title: byTopic.title,
          difficulty: byTopic.difficulty ?? rec.difficulty,
          topic: rec.topic,
        };
      }

      const fallback = takeProblem(() => true);
      return {
        ...rec,
        resolvedId: fallback?.id ?? null,
        title: fallback?.title ?? rec.title,
        difficulty: fallback?.difficulty ?? rec.difficulty,
        topic: rec.topic,
      };
    }),
  }));
}

export function flattenRecommendations(areas, limit = 10) {
  let index = 0;
  const flat = areas.flatMap((area) =>
    area.recommendations.map((problem) => {
      index += 1;
      return {
        ...problem,
        listIndex: index,
        weakAreaId: area.id,
        weakAreaName: area.name,
        weakAreaAccent: area.accent,
        weakAreaAccuracy: area.accuracy,
      };
    })
  );
  return limit ? flat.slice(0, limit) : flat;
}

function collectRecommendationTitles(areas) {
  return [...new Set(
    areas.flatMap((area) => area.recommendations.map((rec) => rec.title).filter(Boolean))
  )];
}

/** Fetch only problems needed to link recommendations — not the full catalog. */
export async function fetchProblemsForRecommendations(getProblems, areas) {
  const emptyFilters = { title: "", difficulty: [], topic: [], status: [] };
  const titles = collectRecommendationTitles(areas);

  const [titlePages, fallbackPage] = await Promise.all([
    Promise.all(
      titles.map((title) =>
        getProblems(0, 5, { ...emptyFilters, title }).catch(() => ({ content: [] }))
      )
    ),
    getProblems(0, 50, emptyFilters).catch(() => ({ content: [] })),
  ]);

  const byId = new Map();
  const add = (list) => {
    for (const p of list ?? []) {
      if (p?.id && !byId.has(p.id)) byId.set(p.id, p);
    }
  };

  titlePages.forEach((page) => add(page.content));
  add(fallbackPage.content);

  return [...byId.values()];
}
