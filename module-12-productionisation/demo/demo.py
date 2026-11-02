"""
Module 12 Demo — Productionisation
Run:  python module-12-productionisation/demo/demo.py

  Part 1: Structured tracing — spans through one request
  Part 2: Circuit breaker — closed, open, half-open, closed
  Part 3: Cost controls — token budget, model tiering, running spend

Parts 1 and 3 need OPENAI_API_KEY. Part 2 runs offline.
"""

from importlib import import_module

from dotenv import load_dotenv

demo_traced_request = import_module("01_tracing").demo_traced_request
demo_circuit_breaker = import_module("02_circuit_breaker").demo_circuit_breaker
demo_cost_controls = import_module("03_cost_controls").demo_cost_controls

DEMOS = {
    "1": ("Structured tracing  (needs a key)", demo_traced_request),
    "2": ("Circuit breaker     (offline)", demo_circuit_breaker),
    "3": ("Cost controls       (needs a key)", demo_cost_controls),
}


def main():
    load_dotenv()

    print("\n" + "=" * 60)
    print("  MODULE 12 DEMO — PRODUCTIONISATION")
    print("=" * 60)
    print("  Parts 1 and 3 call the API. Part 2 runs offline.")

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  a. All")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        if choice == "a":
            print()
            for _, fn in DEMOS.values():
                fn()
            continue
        if choice in DEMOS:
            print()
            DEMOS[choice][1]()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Tracing          — one ID per request, one span per unit of work")
    print("  2. Circuit breaker  — stop calling a dependency that is already down")
    print("  3. Cost controls    — route cheap, cache repeats, refuse over budget")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
