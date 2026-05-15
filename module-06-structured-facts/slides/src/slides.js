export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 6 — Structured Facts',
      subtitle: 'From raw text to verifiable knowledge',
      icon: 'database',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Raw text is unreliable. Structured data is actionable.',
      points: [
        'LLMs can extract typed, validated facts from unstructured logs and reports.',
        'Facts form a knowledge graph — entities, relationships, provenance.',
        'Grounded QA answers from the graph and cites its sources.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Use **structured outputs** (Pydantic + JSON Schema) for reliable typed data.',
        'Build a **fact extraction pipeline** with provenance and confidence.',
        'Construct a **knowledge graph** from entities and relationships.',
        'Implement **grounded QA** that cites source documents.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Structured outputs — why bother?',
      icon: 'file-text',
      points: [
        'Free-text LLM answers are hard to **validate**, **store**, and **query**.',
        'Structured outputs give you **typed fields** you can trust.',
        'Pydantic models define the schema; the LLM fills in the values.',
        'Validation catches errors **before** they reach your database.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Pydantic model as output schema',
      code: `from pydantic import BaseModel, Field

class Fact(BaseModel):
    subject: str = Field(description="The entity the fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="Original sentence")
    confidence: float = Field(ge=0.0, le=1.0)

# LLM returns JSON → Pydantic validates it
fact = Fact.model_validate_json(llm_response)`,
      highlights: [
        'Field constraints (ge, le) catch out-of-range values automatically',
        'model_validate_json raises ValidationError on bad data',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Extraction prompt',
      code: `def build_extraction_prompt(text: str) -> str:
    return (
        "Extract every factual claim from the text below. "
        "Return a JSON array of objects with keys: "
        "subject, predicate, object, source_text, "
        "confidence (0-1).\\n\\n"
        f"Text:\\n{text}"
    )

# Input:  "Alice manages the infrastructure team."
# Output: [{"subject": "Alice", "predicate": "manages",
#           "object": "infrastructure team", ...}]`,
      highlights: [
        'Explicit schema in the prompt keeps the output predictable',
        'Confidence lets you filter low-quality extractions downstream',
      ],
    },
  },
  // ---- Demo: Structured extraction ----
  {
    type: 'title',
    content: {
      title: 'Demo — Structured extraction',
      subtitle: 'Switch to terminal: python demo/01_extraction.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Knowledge graphs ----
  {
    type: 'title',
    content: {
      title: 'Knowledge graphs',
      subtitle: 'Entities, relationships, and multi-hop traversal',
      icon: 'share-2',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Validation and deduplication',
      icon: 'filter',
      points: [
        '**Confidence threshold**: drop facts below 0.7 (configurable).',
        '**Deduplication**: same (subject, predicate, object) → keep highest confidence.',
        '**Provenance**: every fact links back to the source sentence.',
        'Retry on parse failure: ask the LLM to fix its own JSON.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Knowledge graphs',
      icon: 'share-2',
      points: [
        '**Nodes** = entities (people, organisations, products).',
        '**Edges** = relationships (manages, works_at, supplies).',
        'Build from extracted facts: subject → edge → object.',
        'Traversal: "Who is connected to Acme Corp within 2 hops?"',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Building the graph',
      code: `@dataclass
class Entity:
    name: str
    entity_type: str
    attributes: dict[str, str] = field(default_factory=dict)

@dataclass
class Relationship:
    source: str
    target: str
    relation: str

class KnowledgeGraph:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.edges: list[Relationship] = []

    def neighbours(self, name: str) -> list[Relationship]:
        return [e for e in self.edges
                if e.source == name or e.target == name]`,
      highlights: [
        'Simple adjacency list — no external graph database needed',
        'neighbours() enables BFS/DFS traversal for multi-hop queries',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Multi-hop traversal',
      code: `def find_connections(graph, start, max_depth=2):
    visited = set()
    queue = [(start, 0)]
    results = []

    while queue:
        node, depth = queue.pop(0)
        if node in visited or depth > max_depth:
            continue
        visited.add(node)

        for rel in graph.neighbours(node):
            results.append(rel)
            next_node = (rel.target if rel.source == node
                         else rel.source)
            if next_node not in visited:
                queue.append((next_node, depth + 1))

    return results`,
      highlights: [
        'BFS from the starting entity up to max_depth hops',
        'Returns all relationships discovered along the way',
      ],
    },
  },
  // ---- Demo: Knowledge graph ----
  {
    type: 'title',
    content: {
      title: 'Demo — Knowledge graph',
      subtitle: 'Switch to terminal: python demo/02_graph.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Grounded QA ----
  {
    type: 'title',
    content: {
      title: 'Grounded QA',
      subtitle: 'Answering questions with graph evidence and citations',
      icon: 'help-circle',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Grounded QA from the graph',
      icon: 'help-circle',
      points: [
        'Query the graph for relevant entities and relationships.',
        'Build a prompt with the **graph evidence** as context.',
        'Answer must **cite** which entities/relationships it used.',
        'No evidence found → low-confidence answer with a caveat.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Vector RAG vs graph RAG',
      left: {
        label: 'Vector RAG',
        items: [
          'Retrieves text chunks by semantic similarity',
          'Good for "what does the doc say about X?"',
          'Flat — no relationship structure',
          'Simple to build and scale',
        ],
      },
      right: {
        label: 'Graph RAG',
        items: [
          'Traverses entity relationships',
          'Good for "how is X related to Y?"',
          'Multi-hop reasoning built in',
          'Requires extraction pipeline first',
        ],
      },
    },
  },
  // ---- Demo: Grounded QA ----
  {
    type: 'title',
    content: {
      title: 'Demo — Grounded QA',
      subtitle: 'Switch to terminal: python demo/03_grounded_qa.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 6',
      rules: [
        {
          rule: 'Schema is the contract',
          example: 'Pydantic models catch bad data before it enters the graph.',
          icon: 'file-text',
        },
        {
          rule: 'Every fact needs provenance',
          example: 'A fact without a source is an unsupported claim.',
          icon: 'link',
        },
        {
          rule: 'Confidence is not optional',
          example: 'Threshold + dedup = clean, trustworthy knowledge.',
          icon: 'check-square',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Fact extractor: Pydantic schemas and LLM extraction with validation',
        '02 — Knowledge graph: entities, relationships, and multi-hop traversal',
        '03 — Grounded QA: answer questions with citations and confidence scores',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 6 — Complete',
      subtitle: 'Next: agent memory',
      icon: 'check-circle',
    },
  },
];
