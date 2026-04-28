"use client";

import { useMemo, useState } from "react";

type ViewerPanelProps = {
  papers: Array<{
    section?: string;
    title?: string;
    year?: number | string;
    journal?: string;
    link?: string;
  }>;
  sections: string[];
  isOpen: boolean;
  onClose: () => void;
};

export default function ViewerPanel({
  papers,
  sections,
  isOpen,
  onClose,
}: ViewerPanelProps) {
  const [search, setSearch] = useState("");
  const searchTerm = search.trim().toLowerCase();

  const filteredPapers = useMemo(() => {
    if (!searchTerm) return papers;
    return papers.filter((paper) => {
      const section = paper.section ?? "";
      const title = paper.title ?? "";
      const journal = paper.journal ?? "";
      const haystack = `${section} ${title} ${journal}`.toLowerCase();
      return haystack.includes(searchTerm);
    });
  }, [papers, searchTerm]);

  const grouped = new Map<string, ViewerPanelProps["papers"]>();
  for (const paper of filteredPapers) {
    const section = (paper.section ?? "").trim() || "Other";
    if (!grouped.has(section)) grouped.set(section, []);
    grouped.get(section)!.push(paper);
  }

  const orderedSections = [
    ...sections.filter((section) => grouped.has(section)),
    ...[...grouped.keys()].filter((section) => !sections.includes(section)),
  ];

  return (
    <aside
      className={`fixed inset-y-0 right-0 z-50 w-full border-l border-neutral-200 bg-white shadow-xl transition-transform duration-300 ease-out sm:w-1/2 ${
        isOpen ? "translate-x-0" : "translate-x-full"
      }`}
      aria-hidden={!isOpen}
    >
      <div className="flex h-full flex-col p-4 sm:p-6">
        <div className="flex items-start justify-between">
          <h2 className="text-lg font-medium text-neutral-900">Results Viewer</h2>
          <button
            type="button"
            onClick={onClose}
            disabled={!isOpen}
            className="rounded border border-neutral-300 px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-50"
          >
            Close
          </button>
        </div>

        <div className="mt-4 space-y-4 overflow-y-auto pr-1">
          <p className="text-sm text-neutral-700">
            Papers loaded: <span className="font-medium">{papers.length}</span>
          </p>
          <p className="text-sm text-neutral-700">
            Showing: <span className="font-medium">{filteredPapers.length}</span>
          </p>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search papers..."
            aria-label="Search papers"
            className="min-h-10 w-full rounded border border-neutral-300 px-3 text-sm text-neutral-900 outline-none focus:border-neutral-500"
          />

          {orderedSections.length > 0 ? (
            orderedSections.map((section) => {
              const sectionPapers = grouped.get(section) ?? [];
              return (
                <div key={section} className="space-y-2">
                  <h3 className="text-sm font-medium text-neutral-800">{section}</h3>
                  <div className="table-container w-full overflow-x-auto rounded border border-neutral-200">
                    <table className="w-full min-w-[760px] border-collapse text-sm">
                      <thead className="sticky top-0 z-10 bg-neutral-100 text-left text-neutral-700">
                        <tr>
                          <th className="whitespace-nowrap border-b border-neutral-200 px-4 py-2.5 font-medium">
                            Section
                          </th>
                          <th className="whitespace-nowrap border-b border-neutral-200 px-4 py-2.5 font-medium">
                            Title
                          </th>
                          <th className="whitespace-nowrap border-b border-neutral-200 px-4 py-2.5 font-medium">
                            Year
                          </th>
                          <th className="whitespace-nowrap border-b border-neutral-200 px-4 py-2.5 font-medium">
                            Journal
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {sectionPapers.map((paper, idx) => (
                          <tr
                            key={`${section}-${idx}-${paper.title ?? ""}`}
                            className="border-b border-neutral-100 last:border-b-0 odd:bg-white even:bg-neutral-50/60"
                          >
                            <td className="whitespace-nowrap px-4 py-2.5 text-neutral-700">
                              {section}
                            </td>
                            <td className="whitespace-nowrap px-4 py-2.5">
                              {paper.link ? (
                                <a
                                  href={paper.link}
                                  target="_blank"
                                  rel="noreferrer noopener"
                                  title={paper.title || "Untitled"}
                                  className="block max-w-[26rem] truncate text-blue-700 hover:underline"
                                >
                                  {paper.title || "Untitled"}
                                </a>
                              ) : (
                                <span
                                  title={paper.title || "Untitled"}
                                  className="block max-w-[26rem] truncate text-neutral-800"
                                >
                                  {paper.title || "Untitled"}
                                </span>
                              )}
                            </td>
                            <td className="whitespace-nowrap px-4 py-2.5 text-neutral-700">
                              {paper.year ?? ""}
                            </td>
                            <td className="whitespace-nowrap px-4 py-2.5 text-neutral-700">
                              {paper.journal ?? ""}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-sm text-neutral-500">No papers available.</p>
          )}
        </div>
      </div>
    </aside>
  );
}
