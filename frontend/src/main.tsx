import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const queryClient = new QueryClient();

type DocumentStatus = "uploaded" | "queued" | "processing" | "extracting" | "chunking" | "embedding" | "indexed" | "failed";
type Document = {
  id: string;
  original_filename: string;
  media_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
type DocumentList = { items: Document[]; total: number };
type Job = { id: string; document_id: string; status: string; attempts: number; error_message: string | null; created_at: string };
type JobList = { items: Job[]; total: number };
type Answer = { answer: string; citations: Array<{ source_number: number; filename: string; content: string; page_number: number | null }> };

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function App() {
  const [page, setPage] = useState<"overview" | "documents" | "assistant" | "ingestion">("overview");
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">R</span><span>Ragline</span></div>
        <p className="workspace-label">WORKSPACE</p>
        <nav>
          {[
            ["overview", "Overview", "⌂"],
            ["documents", "Documents", "▤"],
            ["assistant", "AI Assistant", "✦"],
            ["ingestion", "Ingestion Monitor", "◌"],
          ].map(([value, label, icon]) => (
            <button className={page === value ? "nav-item active" : "nav-item"} key={value} onClick={() => setPage(value as typeof page)}>
              <span>{icon}</span>{label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer"><span className="status-dot" /> API connected<br /><small>Local workspace</small></div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><p className="eyebrow">Document intelligence</p><h1>{page === "overview" ? "Good morning" : pageLabel(page)}</h1></div><div className="avatar">Z</div></header>
        {page === "overview" && <Overview onNavigate={setPage} />}
        {page === "documents" && <Documents />}
        {page === "assistant" && <Assistant />}
        {page === "ingestion" && <Ingestion />}
      </main>
    </div>
  );
}

function pageLabel(page: string) {
  return ({ documents: "Documents", assistant: "AI Assistant", ingestion: "Ingestion monitor" } as Record<string, string>)[page] ?? "Overview";
}

function Overview({ onNavigate }: { onNavigate: (page: "documents" | "assistant" | "ingestion") => void }) {
  const documents = useQuery({ queryKey: ["documents"], queryFn: () => api<DocumentList>("/documents?page_size=100") });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<JobList>("/ingestion/jobs?limit=100") });
  const docs = documents.data?.items ?? [];
  const indexed = docs.filter((doc) => doc.status === "indexed").length;
  const failed = docs.filter((doc) => doc.status === "failed").length;
  const active = docs.filter((doc) => !["indexed", "failed"].includes(doc.status)).length;
  return <section>
    <div className="hero-card"><div><span className="hero-kicker">Your knowledge base</span><h2>Everything your team knows,<br /><em>ready to be searched.</em></h2><button className="primary-button" onClick={() => onNavigate("documents")}>Upload documents <span>→</span></button></div><div className="hero-orb">✦</div></div>
    {documents.isError && <ErrorBanner message={(documents.error as Error).message} />}
    <div className="metric-grid">
      <Metric label="Total documents" value={documents.data?.total ?? "—"} detail="In this workspace" />
      <Metric label="Indexed" value={indexed} detail="Ready for questions" tone="green" />
      <Metric label="Processing" value={active} detail="In the pipeline" tone="amber" />
      <Metric label="Failed" value={failed} detail="Need attention" tone="red" />
    </div>
    <div className="section-heading"><div><p className="eyebrow">Activity</p><h2>Recent ingestion jobs</h2></div><button className="text-button" onClick={() => onNavigate("ingestion")}>View all →</button></div>
    <JobTable jobs={(jobs.data?.items ?? []).slice(0, 5)} />
  </section>;
}

function Metric({ label, value, detail, tone = "blue" }: { label: string; value: string | number; detail: string; tone?: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}>◈</div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div>;
}

function Documents() {
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const documents = useQuery({ queryKey: ["documents", search], queryFn: () => api<DocumentList>(`/documents?page_size=100${search ? `&search=${encodeURIComponent(search)}` : ""}`) });
  const upload = useMutation({
    mutationFn: (file: File) => { const body = new FormData(); body.append("file", file); return api<Document>("/documents", { method: "POST", body }); },
    onSuccess: () => { setSelectedFile(null); void client.invalidateQueries({ queryKey: ["documents"] }); void client.invalidateQueries({ queryKey: ["jobs"] }); },
  });
  const deleteDocument = useMutation({ mutationFn: (id: string) => api<void>(`/documents/${id}`, { method: "DELETE" }), onSuccess: () => void client.invalidateQueries({ queryKey: ["documents"] }) });
  return <section>
    <div className="toolbar"><div className="search-box"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search documents..." /></div><label className="primary-button upload-button">+ Upload documents<input type="file" multiple accept=".pdf,.docx,.xlsx,.csv,.txt" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} /></label></div>
    {selectedFile && <div className="upload-strip"><span>Ready to upload: <strong>{selectedFile.name}</strong></span><button className="primary-button small" disabled={upload.isPending} onClick={() => upload.mutate(selectedFile)}>{upload.isPending ? "Uploading..." : "Start upload"}</button></div>}
    {upload.isError && <ErrorBanner message={(upload.error as Error).message} />}
    <div className="table-card"><div className="table-header"><span>Document</span><span>Status</span><span>Size</span><span>Uploaded</span><span /></div>{documents.isLoading && <div className="empty-state">Loading documents...</div>}{documents.data?.items.map((document) => <div className="table-row" key={document.id}><div className="document-name"><span className="file-icon">{extension(document.original_filename)}</span><div><strong>{document.original_filename}</strong><small>{document.media_type}</small></div></div><Status status={document.status} /><span>{formatBytes(document.size_bytes)}</span><span>{new Date(document.created_at).toLocaleDateString()}</span><button className="icon-button" title="Delete" onClick={() => deleteDocument.mutate(document.id)}>×</button></div>)}{documents.data?.items.length === 0 && <div className="empty-state">No documents found. Upload a file to begin.</div>}</div>
  </section>;
}

function Assistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const ask = useMutation({
    mutationFn: async (value: string) => {
      const id = conversationId ?? (await api<{ id: string }>("/conversations", { method: "POST" })).id;
      setConversationId(id);
      return api<Answer>(`/conversations/${id}/messages`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: value }) });
    },
    onSuccess: (value) => { setAnswer(value); setQuestion(""); },
  });
  return <section className="assistant-layout"><div className="chat-card"><div className="chat-intro"><span className="assistant-icon">✦</span><h2>Ask your knowledge base</h2><p>Answers are grounded in your indexed documents and include source citations.</p></div>{answer ? <div className="answer"><span className="answer-label">ASSISTANT</span><p>{answer.answer}</p><div className="citations"><strong>Sources</strong>{answer.citations.map((citation) => <div className="citation" key={citation.source_number}><span>[{citation.source_number}]</span><div><strong>{citation.filename}</strong>{citation.page_number && <small>Page {citation.page_number}</small>}<p>{citation.content}</p></div></div>)}</div></div> : <div className="suggestions"><button onClick={() => setQuestion("What documents are available in this workspace?")}>What documents are available?</button><button onClick={() => setQuestion("Summarize the key policies.")}>Summarize the key policies</button></div>}<form className="question-form" onSubmit={(event) => { event.preventDefault(); if (question.trim()) ask.mutate(question); }}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question about your documents..." /><button disabled={ask.isPending || !question.trim()}>{ask.isPending ? "..." : "↑"}</button></form>{ask.isError && <ErrorBanner message={(ask.error as Error).message} />}</div></section>;
}

function Ingestion() {
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<JobList>("/ingestion/jobs?limit=100"), refetchInterval: 5000 });
  return <section><div className="info-banner"><span>◌</span><div><strong>Live ingestion monitor</strong><p>Job statuses refresh automatically every 5 seconds.</p></div></div><div className="table-card"><div className="table-header"><span>Job ID</span><span>Status</span><span>Attempts</span><span>Created</span><span /></div><JobTable jobs={jobs.data?.items ?? []} /></div></section>;
}

function JobTable({ jobs }: { jobs: Job[] }) {
  if (!jobs.length) return <div className="empty-state">No ingestion jobs yet.</div>;
  return <>{jobs.map((job) => <div className="table-row" key={job.id}><div className="document-name"><span className="file-icon">↗</span><div><strong>{job.id.slice(0, 8)}…</strong><small>{job.document_id.slice(0, 8)}…</small></div></div><Status status={job.status as DocumentStatus} /><span>{job.attempts}</span><span>{new Date(job.created_at).toLocaleString()}</span><span /></div>)}</>;
}

function Status({ status }: { status: string }) { return <span className={`status ${status}`}><i />{status}</span>; }
function ErrorBanner({ message }: { message: string }) { return <div className="error-banner">⚠ {message}</div>; }
function extension(name: string) { return name.split(".").pop()?.toUpperCase() ?? "FILE"; }
function formatBytes(bytes: number) { return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`; }

createRoot(document.getElementById("root")!).render(<StrictMode><QueryClientProvider client={queryClient}><App /></QueryClientProvider></StrictMode>);
