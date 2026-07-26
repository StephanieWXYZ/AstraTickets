import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";

import {
  addKnowledgeDocument,
  ApiError,
  searchKnowledge,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type {
  KnowledgeDocumentResult,
  KnowledgeSearchResult,
} from "../types";

const MAX_FILE_SIZE = 1_000_000;

export function KnowledgeBasePage() {
  const { user, token, signOut } = useAuth();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [text, setText] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploadResult, setUploadResult] = useState<KnowledgeDocumentResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [query, setQuery] = useState("");
  const [searchError, setSearchError] = useState("");
  const [searchResult, setSearchResult] = useState<KnowledgeSearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError("");
    setUploadResult(null);
    if (file.size > MAX_FILE_SIZE) {
      setUploadError("Choose a text or Markdown file smaller than 1 MB.");
      event.target.value = "";
      return;
    }
    const extension = file.name.toLowerCase().split(".").pop();
    if (extension !== "txt" && extension !== "md") {
      setUploadError("Only .txt and .md files are supported.");
      event.target.value = "";
      return;
    }
    try {
      const contents = await file.text();
      setText(contents);
      setSource(file.name);
      if (!title) {
        setTitle(file.name.replace(/\.(txt|md)$/i, "").replaceAll(/[-_]+/g, " "));
      }
    } catch {
      setUploadError("We could not read this file. Please choose it again.");
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setIsUploading(true);
    setUploadError("");
    setUploadResult(null);
    try {
      const result = await addKnowledgeDocument(token, { title, source, text });
      setUploadResult(result);
      setTitle("");
      setSource("");
      setText("");
    } catch (error) {
      setUploadError(
        error instanceof ApiError
          ? error.message
          : "We could not add this document. Please try again.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setIsSearching(true);
    setSearchError("");
    try {
      setSearchResult(await searchKnowledge(token, query));
    } catch (error) {
      setSearchError(
        error instanceof ApiError
          ? error.message
          : "We could not search the knowledge base. Please try again.",
      );
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <main className="workspace knowledge-workspace">
      <header className="workspace-header">
        <Link className="brand" to="/staff/dashboard">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>AstraTickets</span>
        </Link>
        <div className="account-actions">
          <Link className="header-link" to="/staff/dashboard">Support queue</Link>
          <span className="account-name">{user?.full_name} · administrator</span>
          <button className="button button-quiet" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <section className="knowledge-intro">
        <p className="eyebrow">Administrator tools</p>
        <h1>Knowledge base</h1>
        <p>Add trusted support information and check what the assistant can retrieve.</p>
      </section>

      <div className="knowledge-grid">
        <section className="panel knowledge-panel" aria-labelledby="add-knowledge-title">
          <div className="panel-heading">
            <p className="eyebrow">Add information</p>
            <h2 id="add-knowledge-title">New document</h2>
          </div>
          <form onSubmit={handleUpload}>
            <label className="file-picker">
              Choose a text file
              <input type="file" accept=".txt,.md,text/plain,text/markdown" onChange={handleFile} />
              <span className="field-help">Plain text or Markdown, up to 1 MB.</span>
            </label>
            <div className="field-pair">
              <label>
                Document title
                <input
                  required
                  maxLength={500}
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Password reset policy"
                />
              </label>
              <label>
                Source
                <input
                  required
                  maxLength={500}
                  value={source}
                  onChange={(event) => setSource(event.target.value)}
                  placeholder="password-reset.md"
                />
              </label>
            </div>
            <label>
              Document text
              <textarea
                required
                minLength={20}
                maxLength={MAX_FILE_SIZE}
                rows={13}
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Paste trusted support information here."
              />
            </label>
            {uploadError && <div className="form-error" role="alert">{uploadError}</div>}
            {uploadResult && (
              <div className="form-success" role="status">
                Document added as {uploadResult.chunks_added} searchable
                {uploadResult.chunks_added === 1 ? " chunk" : " chunks"}.
              </div>
            )}
            <button className="button button-primary" type="submit" disabled={isUploading}>
              {isUploading ? "Adding document…" : "Add to knowledge base"}
            </button>
          </form>
        </section>

        <section className="panel knowledge-panel" aria-labelledby="test-knowledge-title">
          <div className="panel-heading">
            <p className="eyebrow">Retrieval preview</p>
            <h2 id="test-knowledge-title">Test a question</h2>
          </div>
          <form className="knowledge-search-form" onSubmit={handleSearch}>
            <label>
              Support question
              <textarea
                required
                maxLength={1000}
                rows={4}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="How long does a password reset link last?"
              />
            </label>
            {searchError && <div className="form-error" role="alert">{searchError}</div>}
            <button className="button button-quiet" type="submit" disabled={isSearching}>
              {isSearching ? "Searching…" : "Search knowledge"}
            </button>
          </form>

          {searchResult && (
            <div className="knowledge-results" aria-live="polite">
              <div className="knowledge-result-summary">
                <strong>{searchResult.matches.length} matches</strong>
                <span>{searchResult.retrieval_ms.toFixed(1)} ms</span>
              </div>
              {searchResult.matches.length === 0 ? (
                <p className="knowledge-empty">
                  No matching information was found. The AI would ask for human help.
                </p>
              ) : (
                searchResult.matches.map((match) => (
                  <article className="knowledge-match" key={match.chunk_id}>
                    <header>
                      <div>
                        <strong>{match.title}</strong>
                        <span>{match.source}</span>
                      </div>
                      <span>{Math.round(match.score * 100)}% relevance</span>
                    </header>
                    <p>{match.text}</p>
                  </article>
                ))
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
