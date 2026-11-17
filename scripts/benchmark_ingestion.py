"""Generate a reproducible corpus for measuring ingestion and retrieval throughput."""

import argparse
import time
from pathlib import Path


def generate_documents(output_dir: Path, count: int) -> float:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    for index in range(count):
        (output_dir / f"benchmark-{index:05d}.txt").write_text(
            f"Benchmark document {index}\n"
            "The retention policy requires records to be preserved for seven years.\n"
            "This generated corpus is for local performance testing only.\n",
            encoding="utf-8",
        )
    return time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("benchmark-data"))
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    duration = generate_documents(args.output, args.count)
    print(f"Generated {args.count} documents in {duration:.2f}s at {args.output}")


if __name__ == "__main__":
    main()
