from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings


@dataclass(frozen=True)
class DocumentSpec:
    slug: str
    url: str
    content_selector: str | None = None
    file_name: str | None = None


DEFAULT_DOCUMENTS: tuple[DocumentSpec, ...] = (
    DocumentSpec(
        slug="wafr_framework_overview",
        url="https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_operational_excellence",
        url="https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_security_pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_reliability_pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_performance_efficiency_pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_cost_optimization_pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_sustainability_pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/welcome.html",
        content_selector="main",
    ),
    DocumentSpec(
        slug="wafr_framework_whitepaper",
        url=(
            "https://docs.aws.amazon.com/wellarchitected/latest/framework/"
            "AWS_Well-Architected_Framework.pdf"
        ),
        file_name="aws_well_architected_framework.pdf",
    ),
)


class WAFRScraper:
    def __init__(
        self,
        output_dir: Path | None = None,
        request_timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        if output_dir is not None:
            self.output_dir = output_dir.resolve()
        else:
            self.output_dir = settings.scraper_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.request_timeout = request_timeout or settings.scraper_request_timeout

        self._client = httpx.Client(
            timeout=self.request_timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
            },
            follow_redirects=True,
        )

    def scrape(self, documents: Iterable[DocumentSpec] | None = None) -> list[Path]:
        docs = list(documents or DEFAULT_DOCUMENTS)
        saved_files: list[Path] = []
        for spec in docs:
            result = self._scrape_single(spec)
            if result:
                saved_files.append(result)
            time.sleep(1)  # be kind to origin
        return saved_files

    def _scrape_single(self, spec: DocumentSpec) -> Path | None:
        try:
            response = self._client.get(spec.url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"[warn] Failed to fetch {spec.url}: {exc}", file=sys.stderr)
            return None

        if self._is_pdf(spec.url):
            file_name = spec.file_name or f"{spec.slug}.pdf"
            path = self.output_dir / file_name
            path.write_bytes(response.content)
            return path

        html_text = response.text
        cleaned = self._extract_text(html_text, spec.content_selector)
        self._write_jsonl(spec.slug, spec.url, cleaned)
        return self.output_dir / f"{spec.slug}.jsonl"

    @staticmethod
    def _is_pdf(url: str) -> bool:
        return url.lower().endswith(".pdf")

    @staticmethod
    def _extract_text(html: str, selector: str | None) -> str:
        soup = BeautifulSoup(html, "lxml")
        node = soup.select_one(selector) if selector else soup.body
        if not node:
            node = soup.body

        paragraphs: list[str] = []
        for element in node.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5"]):
            text = element.get_text(separator=" ", strip=True)
            if not text:
                continue
            text = re.sub(r"\s+", " ", text)
            paragraphs.append(text)
        return "\n".join(paragraphs)

    def _write_jsonl(self, slug: str, source_url: str, content: str) -> None:
        payload = {
            "id": slug,
            "source": source_url,
            "content": content,
        }
        path = self.output_dir / f"{slug}.jsonl"
        path.write_text(
            json.dumps(payload, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _load_specs_from_file(path: Path) -> Sequence[DocumentSpec]:
    with path.open(encoding="utf-8") as stream:
        parsed = json.load(stream)
    documents: list[DocumentSpec] = []
    for item in parsed:
        documents.append(
            DocumentSpec(
                slug=item["slug"],
                url=item["url"],
                content_selector=item.get("content_selector"),
                file_name=item.get("file_name"),
            )
        )
    return documents


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download AWS Well-Architected Framework documentation locally."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Directory where scraped documents should be stored (defaults to data/raw).",
    )
    parser.add_argument(
        "--specs-file",
        type=Path,
        default=None,
        help="Optional JSON file describing additional document specs to fetch.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)

    scraper = WAFRScraper(output_dir=args.output)

    documents: Iterable[DocumentSpec] = DEFAULT_DOCUMENTS
    if args.specs_file and args.specs_file.exists():
        documents = _load_specs_from_file(args.specs_file)

    saved = scraper.scrape(documents)
    for path in saved:
        print(path)  # noqa: T201


if __name__ == "__main__":
    main()
