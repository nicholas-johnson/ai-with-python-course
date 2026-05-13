"""
Demo: Modules, __main__, argparse, and logging.
Run:  python module-00-python-fundamentals/demo/02_modules_cli.py --department science
      python module-00-python-fundamentals/demo/02_modules_cli.py --min-clearance 4
"""

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pathfinder.crew")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_crew() -> list[dict]:
    path = DATA_DIR / "crew.json"
    logger.info("Loading crew manifest from %s", path)
    return json.loads(path.read_text())


def filter_crew(
    crew: list[dict],
    department: str | None = None,
    min_clearance: int = 0,
) -> list[dict]:
    result = crew
    if department:
        result = [m for m in result if m["department"] == department]
        logger.info("Filtered to department=%s (%d members)", department, len(result))
    if min_clearance > 0:
        result = [m for m in result if m["clearanceLevel"] >= min_clearance]
        logger.info("Filtered to clearance>=%d (%d members)", min_clearance, len(result))
    return result


def print_roster(members: list[dict]) -> None:
    if not members:
        print("No crew match the given filters.")
        return
    print(f"\n{'Name':<30} {'Role':<20} {'Clearance':<10} {'Mission'}")
    print("-" * 80)
    for m in members:
        mission = m["activeMission"] or "—"
        print(f"{m['name']:<30} {m['role']:<20} {m['clearanceLevel']:<10} {mission}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DSS Pathfinder — crew manifest query tool",
    )
    parser.add_argument("--department", "-d", help="Filter by department")
    parser.add_argument(
        "--min-clearance", "-c", type=int, default=0,
        help="Minimum clearance level (1-5)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    crew = load_crew()
    filtered = filter_crew(crew, department=args.department, min_clearance=args.min_clearance)
    print_roster(filtered)
