import { useState, type FormEvent } from "react";
import "./App.css";

type ImageResult = {
  id: number | string | null;
  title: string;
  image_url: string;
  original_url?: string;
  source: string;
  source_url?: string;
  width?: number;
  height?: number;
};

type SearchResponse = {
  query: string;
  count: number;
  images: ImageResult[];
};

const API_URL = "http://localhost:3000";

function App() {
  const [query, setQuery] = useState("");
  const [images, setImages] = useState<ImageResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState("");
  const [searchMode, setSearchMode] = useState<"web" | "local">("web");
  const [subject, setSubject] = useState("All");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      setError("Please enter at least 2 characters.");
      return;
    }

    setLoading(true);
    setError("");
    setImages([]);
    setSearched(trimmedQuery);

    try {
      const params = new URLSearchParams({
        q: trimmedQuery,
        limit: "20",
      });

      const endpoint =
        searchMode === "local" ? "/api/local-images/search" : "/api/images";

      if (searchMode === "local" && subject !== "All") {
        params.set("subject", subject);
      }

      const response = await fetch(
        `${API_URL}${endpoint}?${params.toString()}`,
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Something went wrong during image search.",
        );
      }

      const result = data as SearchResponse;
      setImages(result.images);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="hero">
        <span className="eyebrow">IMAGE DISCOVERY</span>
        <h1>Find images for anything.</h1>
        <p>
          Search the web for illustrations, diagrams, photographs, and visual
          references.
        </p>

        <form className="search-form" onSubmit={handleSearch}>
          <span className="search-icon" aria-hidden="true">
            ⌕
          </span>

          <input
            type="search"
            placeholder={
              searchMode === "local"
                ? "Search your local image collection..."
                : "Search images on the web..."
            }
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search images"
          />

          <button type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="suggestions">
          <span>Try:</span>
          {[
            "knee anatomy",
            "solar system diagram",
            "minimalist architecture",
          ].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setQuery(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>

        <div className="search-tabs">
          <button
            type="button"
            className={searchMode === "web" ? "active" : ""}
            onClick={() => {
              setSearchMode("web");
              setError("");
            }}
          >
            Web Search
          </button>

          <button
            type="button"
            className={searchMode === "local" ? "active" : ""}
            onClick={() => {
              setSearchMode("local");
              setError("");
            }}
          >
            Local Image Pool
          </button>
        </div>

        {searchMode === "local" && (
          <div className="local-filters">
            <label htmlFor="subject-filter">Subject</label>

            <select
              id="subject-filter"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
            >
              <option value="All">All subjects</option>
              <option value="Biology">Biology</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
            </select>
          </div>
        )}
      </header>

      <section className="results-section">
        <div className="results-heading">
          <div>
            <h2>
              {loading
                ? "Finding images..."
                : searched
                  ? `Results for "${searched}"`
                  : "Explore images"}
            </h2>

            <p>
              {loading
                ? "Please wait while we search."
                : `${images.length} images displayed`}
            </p>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {!loading && !error && images.length === 0 && (
          <div className="empty-state">
            <span className="empty-icon">▧</span>
            <h3>No images to display yet</h3>
            <p>Enter a query above to start your first search.</p>
          </div>
        )}

        <div className="image-grid">
          {images.map((image, index) => (
            <article
              className="image-card"
              key={`${image.id ?? "image"}-${index}`}
            >
              <a
                className="image-preview"
                href={image.source_url || image.original_url || image.image_url}
                target="_blank"
                rel="noopener noreferrer"
                title="Open original source"
              >
                <img
                  src={image.image_url}
                  alt={image.title}
                  loading="lazy"
                  onError={(event) => {
                    const img = event.currentTarget;

                    if (image.original_url && img.src !== image.original_url) {
                      img.src = image.original_url;
                    } else {
                      img.style.visibility = "hidden";
                    }
                  }}
                />
                <span className="open-overlay">Open source ↗</span>
              </a>

              <div className="image-info">
                <h3 title={image.title}>{image.title}</h3>
                <p>{image.source}</p>
                {image.width && image.height && (
                  <span className="dimensions">
                    {image.width} × {image.height}
                  </span>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <footer>
        Search powered by SerpApi · Images belong to their respective sources.
      </footer>
    </main>
  );
}

export default App;
