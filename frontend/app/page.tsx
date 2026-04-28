"use client";

import { useEffect, useState } from "react";
import ViewerPanel from "./components/ViewerPanel";

const BACKEND_ORIGIN =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";
const FREE_USAGE_LIMIT = 5;

const LIMIT_OPTIONS = [
  { value: 5, label: "5" },
  { value: 10, label: "10" },
  { value: 20, label: "20" },
  { value: 50, label: "50" },
  { value: 100, label: "100 - Deep search" },
  { value: 150, label: "150 - Extensive" },
] as const;

type Section = {
  name: string;
  query: string;
  type: "review" | "research";
};

type PapersResponse = {
  keywords: string[];
  sections: Section[];
  papers: unknown[];
};

type PaperRecord = {
  pmid?: string;
  title?: string;
  year?: number | string;
  journal?: string;
  authors?: string[] | string;
  publication_type?: string[] | string;
  doi?: string;
  keywords?: string[] | string;
  abstract?: string;
  section?: string;
  link?: string;
};

function slugify(value: string): string {
  const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return slug || "papers";
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function listToCell(value: string[] | string | undefined): string {
  if (Array.isArray(value)) return value.join("; ");
  return value ?? "";
}

function papersToCsvString(papers: PaperRecord[]): string {
  const header = [
    "PMID",
    "Title",
    "Year",
    "Journal",
    "Authors",
    "PublicationType",
    "DOI",
    "Keywords",
    "Abstract",
    "Section",
    "Link",
  ];
  const lines = [header.join(",")];
  for (const paper of papers) {
    const row = [
      String(paper.pmid ?? ""),
      String(paper.title ?? ""),
      String(paper.year ?? ""),
      String(paper.journal ?? ""),
      listToCell(paper.authors),
      listToCell(paper.publication_type),
      String(paper.doi ?? ""),
      listToCell(paper.keywords),
      String(paper.abstract ?? ""),
      String(paper.section ?? ""),
      String(paper.link ?? ""),
    ];
    lines.push(row.map(csvEscape).join(","));
  }
  return lines.join("\n");
}

export default function Home() {
  const [topic, setTopic] = useState("");
  const [limit, setLimit] = useState(10);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [sections, setSections] = useState<string[]>([]);
  const [papers, setPapers] = useState<PaperRecord[]>([]);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<
    "generate" | "download" | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [usageCount, setUsageCount] = useState(0);
  const [keyModalOpen, setKeyModalOpen] = useState(false);
  const [girlfriendKeyInput, setGirlfriendKeyInput] = useState("");
  const [showGirlfriendKey, setShowGirlfriendKey] = useState(false);
  const [girlfriendKeyError, setGirlfriendKeyError] = useState("");
  const [lastGeneratedTopic, setLastGeneratedTopic] = useState("");
  const [lastGeneratedLimit, setLastGeneratedLimit] = useState<number>(10);
  const hasResults =
    keywords.length > 0 || sections.length > 0 || papers.length > 0;
  const normalizedTopic = topic.trim().toLowerCase();
  const normalizedLastGeneratedTopic = lastGeneratedTopic.trim().toLowerCase();
  const limitChangedSinceLastGenerate = limit !== lastGeneratedLimit;
  const isOutdated =
    hasResults &&
    (normalizedTopic.length > 0 &&
      normalizedTopic !== normalizedLastGeneratedTopic ||
      limitChangedSinceLastGenerate);
  const showGenerateButton =
    !hasResults ||
    normalizedTopic !== normalizedLastGeneratedTopic ||
    limitChangedSinceLastGenerate;
  const disableGenerate = loading || normalizedTopic.length === 0;
  const freeUsesLeft = Math.max(0, FREE_USAGE_LIMIT - usageCount);

  useEffect(() => {
    setIsUnlocked(localStorage.getItem("isUnlocked") === "true");
    const stored = Number.parseInt(localStorage.getItem("usageCount") ?? "0", 10);
    setUsageCount(Number.isFinite(stored) && stored >= 0 ? stored : 0);
    setIsLoaded(true);
  }, []);

  function buildRequestUrl(format: "json" | "csv"): string {
    const params = new URLSearchParams({
      query: topic.trim(),
      limit: String(limit),
      format,
    });
    return `${BACKEND_ORIGIN}/papers?${params}`;
  }

  async function handleGenerateResults() {
    const q = topic.trim();
    if (!q || loading) return;

    if (!isUnlocked) {
      const current = Number.parseInt(localStorage.getItem("usageCount") ?? "0", 10);
      const safeCurrent = Number.isFinite(current) && current >= 0 ? current : 0;
      if (safeCurrent >= FREE_USAGE_LIMIT) {
        setUsageCount(safeCurrent);
        setKeyModalOpen(true);
        setGirlfriendKeyError("");
        return;
      }
      const next = safeCurrent + 1;
      localStorage.setItem("usageCount", String(next));
      setUsageCount(next);
    }

    setError(null);
    setAlertMessage(null);
    setKeywords([]);
    setSections([]);
    setPapers([]);
    setViewerOpen(false);
    setLoading(true);
    setActiveAction("generate");

    try {
      const response = await fetch(buildRequestUrl("json"));
      if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
          const err = (await response.json()) as { detail?: string };
          if (typeof err.detail === "string" && err.detail.trim()) {
            message = err.detail.trim();
          }
        } catch {
          // ignore parse issues and keep fallback
        }
        if (response.status === 422) {
          setAlertMessage(message);
          setError(message);
          setTopic("");
          return;
        }
        throw new Error(message);
      }

      const payload = (await response.json()) as PapersResponse;
      setKeywords(payload.keywords ?? []);
      setSections((payload.sections ?? []).map((section) => section.name));
      setPapers((payload.papers ?? []) as PaperRecord[]);
      setLastGeneratedTopic(q);
      setLastGeneratedLimit(limit);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
      setActiveAction(null);
    }
  }

  function handleDownload() {
    if (papers.length === 0) return;

    setError(null);
    setLoading(true);
    setActiveAction("download");

    try {
      const csvText = papersToCsvString(papers);
      const blob = new Blob([csvText], { type: "text/csv;charset=utf-8" });
      const objectUrl = URL.createObjectURL(blob);
      const filename = `${slugify(keywords[0] ?? "papers")}_papers.csv`;

      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
      setActiveAction(null);
    }
  }

  function handleGirlfriendKeySubmit() {
    const candidate = girlfriendKeyInput.trim();
    if (candidate === "Tuesday") {
      localStorage.setItem("isUnlocked", "true");
      setIsUnlocked(true);
      setGirlfriendKeyInput("");
      setShowGirlfriendKey(false);
      setGirlfriendKeyError("");
      setKeyModalOpen(false);
      return;
    }
    setGirlfriendKeyError("Incorrect key 💔");
  }

  return (
    <div className="min-h-screen w-full bg-neutral-50 px-4 py-8 sm:px-6">
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <main
          className={`w-full max-w-[600px] space-y-6 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm transition-[margin,transform] duration-300 ease-out sm:p-8 ${
            viewerOpen ? "sm:mr-[50%]" : "sm:mr-0"
          }`}
        >
      <h1 className="text-2xl font-medium text-neutral-900">
        Literature Review Generator
      </h1>
      {isLoaded && !isUnlocked ? (
        usageCount >= FREE_USAGE_LIMIT ? (
          <button
            type="button"
            onClick={() => {
              setGirlfriendKeyError("");
              setKeyModalOpen(true);
            }}
            className="text-sm text-pink-700 underline-offset-4 hover:underline"
          >
            Enter Girlfriend Key 💖
          </button>
        ) : null
      ) : isLoaded ? (
        <p className="text-sm text-green-700">Girlfriend Key unlocked 💖</p>
      ) : null}

      <div className="flex flex-col gap-4">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="min-h-10 w-full rounded border border-neutral-300 px-3 text-sm text-neutral-900 outline-none focus:border-neutral-500"
          placeholder="Topic or keywords"
          aria-label="Topic or keywords"
        />
        {!isUnlocked ? (
          <p className="text-xs text-neutral-500">
            Free uses left: {isLoaded ? freeUsesLeft : "—"}
          </p>
        ) : null}
        {isOutdated ? (
          <p className="text-xs text-amber-700">
            Search parameters changed. Click Generate Results to refresh results.
          </p>
        ) : null}
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-neutral-600">
            Number of papers
          </span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            aria-label="Number of papers"
            className="min-h-10 w-full rounded border border-neutral-300 bg-white px-3 text-sm text-neutral-900 outline-none focus:border-neutral-500"
          >
            {LIMIT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        {!hasResults ? (
          showGenerateButton ? (
            <button
              type="button"
              onClick={handleGenerateResults}
              disabled={disableGenerate}
              className="min-h-10 w-full rounded border border-neutral-900 bg-neutral-900 px-4 text-sm text-white hover:bg-neutral-800 disabled:opacity-50 sm:w-auto sm:self-start"
            >
              {loading && activeAction === "generate" ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/50 border-t-white" />
                  Generating...
                </span>
              ) : (
                "Generate Results"
              )}
            </button>
          ) : null
        ) : (
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            {showGenerateButton ? (
              <button
                type="button"
                onClick={handleGenerateResults}
                disabled={disableGenerate}
                className="min-h-10 flex-1 rounded border border-neutral-900 bg-neutral-900 px-4 text-sm text-white hover:bg-neutral-800 disabled:opacity-50 sm:flex-none"
              >
                {loading && activeAction === "generate" ? (
                  <span className="inline-flex items-center gap-2">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/50 border-t-white" />
                    Generating...
                  </span>
                ) : (
                  "Generate Results"
                )}
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => setViewerOpen(true)}
              disabled={loading}
              className="min-h-10 flex-1 rounded border border-neutral-900 bg-neutral-900 px-4 text-sm text-white hover:bg-neutral-800 disabled:opacity-50 sm:flex-none"
            >
              View Results
            </button>
            <button
              type="button"
              onClick={handleDownload}
              disabled={loading}
              className="min-h-10 flex-1 rounded border border-neutral-300 bg-white px-4 text-sm text-neutral-900 hover:bg-neutral-50 disabled:opacity-50 sm:flex-none"
            >
              {loading && activeAction === "download" ? "…" : "Download CSV"}
            </button>
          </div>
        )}
      </div>
      {hasResults ? (
        <div className="space-y-4">
          {keywords.length > 0 ? (
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-neutral-800">Keywords</h2>
              <div className="flex flex-wrap gap-2">
                {keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="rounded-full border border-neutral-300 px-2.5 py-1 text-xs text-neutral-700"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
          {sections.length > 0 ? (
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-neutral-800">Sections</h2>
              <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                {sections.map((section) => (
                  <li key={section}>{section}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
      <ViewerPanel
        papers={papers}
        sections={sections}
        isOpen={viewerOpen}
        onClose={() => setViewerOpen(false)}
      />

      {alertMessage ? (
        <div
          role="alert"
          className="fixed right-4 top-4 z-[60] max-w-sm rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <p>{alertMessage}</p>
            <button
              type="button"
              onClick={() => setAlertMessage(null)}
              className="rounded px-1 text-amber-900 hover:bg-amber-100"
              aria-label="Dismiss alert"
            >
              ×
            </button>
          </div>
        </div>
      ) : null}

      {keyModalOpen ? (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
            <h2 className="text-lg font-medium text-neutral-900">
              Enter Girlfriend Key 💖
            </h2>
            <div className="mt-4 flex items-center rounded border border-neutral-300 focus-within:border-neutral-500">
              <input
                type={showGirlfriendKey ? "text" : "password"}
                value={girlfriendKeyInput}
                onChange={(e) => setGirlfriendKeyInput(e.target.value)}
                className="min-h-10 w-full rounded-l px-3 text-sm text-neutral-900 outline-none"
                placeholder="Enter key"
                aria-label="Girlfriend key"
              />
              <button
                type="button"
                onClick={() => setShowGirlfriendKey((v) => !v)}
                className="mr-1 rounded px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-100"
                aria-label={showGirlfriendKey ? "Hide key" : "Show key"}
              >
                {showGirlfriendKey ? "Hide" : "Show"}
              </button>
            </div>
            {girlfriendKeyError ? (
              <p className="mt-2 text-sm text-rose-600">{girlfriendKeyError}</p>
            ) : null}
            <div className="mt-4 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setKeyModalOpen(false);
                  setShowGirlfriendKey(false);
                  setGirlfriendKeyError("");
                }}
                className="rounded border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleGirlfriendKeySubmit}
                className="rounded border border-pink-600 bg-pink-600 px-3 py-1.5 text-sm text-white hover:bg-pink-500"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
        </main>
      </div>
    </div>
  );
}
