# Exercise 01 — Dataclass Filtering

Parse JSON records into typed dataclasses, filter by field values, and produce formatted output.

## Objectives

1. Define a `CrewMember` **dataclass** that models a crew record.
2. Implement `load_crew(path)` — read `crew.json` and return a list of `CrewMember` instances.
3. Implement `filter_crew(crew, department, min_clearance)` — filter the list by department (optional) and minimum clearance level.
4. Implement `format_roster(crew)` — return a formatted multi-line string with name, role, and clearance for each member.

## Run the tests

```bash
pytest module-00-python-fundamentals/exercises/01-dataclass-filtering/test_start.py -v
```

## Hints

- Use `@dataclass` with type annotations. Use `field(default_factory=list)` for mutable defaults.
- `json.loads` returns plain dicts — you need to unpack them into your dataclass.
- `format_roster` should return one line per crew member: `"Name (role) — clearance N"`.
