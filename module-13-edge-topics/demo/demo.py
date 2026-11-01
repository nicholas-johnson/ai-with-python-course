"""
Module 13 Demo — Edge Topics
Run:  python module-13-edge-topics/demo/demo.py

  Part 1: Reciprocal rank fusion on two short lists
  Part 2: Hybrid search over ship documents
  Part 3: Agentic RAG
  Part 4: Citation verification
  Part 5: Semantic cache

Parts 2–5 need OPENAI_API_KEY. The 13_* and 14_* scripts are separate.
"""

from importlib import import_module

from dotenv import load_dotenv

demo_rrf = import_module("01_rrf").demo_rrf
demo_hybrid_search = import_module("02_hybrid_search").demo_hybrid_search
demo_agentic_rag = import_module("03_agentic_rag").demo_agentic_rag
demo_citation_verification = import_module("04_citations").demo_citation_verification
demo_semantic_caching = import_module("05_semantic_cache").demo_semantic_caching

DEMOS = {
    "1": ("Reciprocal rank fusion", demo_rrf),
    "2": ("Hybrid search", demo_hybrid_search),
    "3": ("Agentic RAG", demo_agentic_rag),
    "4": ("Citation verification", demo_citation_verification),
    "5": ("Semantic cache", demo_semantic_caching),
}


def main():
    load_dotenv()

    print("\n" + "=" * 60)
    print("  MODULE 13 DEMO — EDGE TOPICS")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. RRF              — fuse two rankings with 1/(k + rank)")
    print("  2. Hybrid search    — keyword plus vector, then RRF")
    print("  3. Agentic RAG      — the model decides what to retrieve")
    print("  4. Citations        — every claim needs a source")
    print("  5. Semantic cache   — a paraphrase should not cost another call")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
