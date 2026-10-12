import json
import os
from typing import Any
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

app = FastAPI(title="Image Search API")

# Allow requests from the local Vite development server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
METADATA_FILE = BASE_DIR / "image_metadata.json"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Expose local images through HTTP URLs.
app.mount(
    "/images",
    StaticFiles(directory=str(IMAGES_DIR)),
    name="images",
)



@app.get("/")
async def root():
    return {
        "message": "Image Search API is running",
        "docs": "/docs",
    }


@app.get("/api/images")
async def search_images(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
):
    if not SERPAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SERPAPI_API_KEY is missing from backend/.env",
        )

    params = {
        "engine": "google_images",
        "q": q.strip(),
        "api_key": SERPAPI_API_KEY,
        "hl": "en",
        "gl": "in",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search.json",
                params=params,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Image search timed out. Please try again.",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="The image search provider returned an error.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the image search provider.",
        )

    if data.get("error"):
        raise HTTPException(
            status_code=502,
            detail=str(data["error"]),
        )

    results = []

    for item in data.get("images_results", [])[:limit]:
        # Prefer the thumbnail for more reliable gallery loading.
        # Fall back to the original image if necessary.
        image_url = item.get("thumbnail") or item.get("original")

        if not image_url:
            continue

        results.append({
            "id": item.get("position"),
            "title": item.get("title") or "Untitled image",
            "image_url": image_url,
            "original_url": item.get("original"),
            "source": item.get("source") or "Unknown source",
            "source_url": item.get("link"),
            "width": item.get("original_width"),
            "height": item.get("original_height"),
        })

    return {
        "query": q.strip(),
        "count": len(results),
        "images": results,
    }



@app.get("/api/local-images/search")
async def search_local_images(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200),
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    if not METADATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="Image metadata JSON file was not found.",
        )

    try:
        with METADATA_FILE.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Could not read image metadata JSON.",
        )

    if not isinstance(metadata, list):
        raise HTTPException(
            status_code=500,
            detail="Image metadata must contain a JSON array.",
        )

    query = q.strip().casefold()
    results = []

    for item in metadata:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", ""))
        item_subject = str(item.get("subject", ""))
        tags = item.get("tags", [])

        if not isinstance(tags, list):
            tags = []

        # Optional subject filter.
        if subject and item_subject.casefold() != subject.strip().casefold():
            continue

        # Keyword search across title, subject, and tags.
        searchable_text = " ".join([
            title,
            item_subject,
            *[str(tag) for tag in tags],
        ]).casefold()

        if query not in searchable_text:
            continue

        filename = item.get("filename")

        # Only allow a filename, not an arbitrary filesystem path.
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
        ):
            continue

        image_path = IMAGES_DIR / filename

        if not image_path.is_file():
            continue

        results.append({
            "id": item.get("id"),
            "title": title,
            "subject": item_subject,
            "tags": tags,
            "image_url": (
                f"{str(request.base_url).rstrip('/')}/images/{filename}"
            )
        })

        if len(results) >= limit:
            break

    return {
        "query": q.strip(),
        "count": len(results),
        "images": results,
    }
