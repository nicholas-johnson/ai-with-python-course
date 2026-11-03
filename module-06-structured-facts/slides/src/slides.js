export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 6 — Graphs & Structured Facts',
      subtitle: 'From raw text to verifiable knowledge',
      icon: 'database',
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
        'Expose the graph as **MCP tools** an agent loop can call.',
      ],
    },
  },

  // ---- Section: Structured outputs ----
  {
    type: 'title',
    content: {
      title: 'Structured Outputs',
      subtitle: 'Typed fields the model must follow',
      icon: 'file-text',
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

class FactList(BaseModel):   # top level must be an object
    facts: list[Fact]`,
      highlights: [
        'Field descriptions go into the JSON Schema the model sees',
        'Field constraints (ge, le) are part of the schema and re-checked by Pydantic',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Structured outputs — the schema is the format',
      code: `response = client.responses.parse(
    model=MODEL,
    reasoning={"effort": "none"},
    text_format=FactList,
    input=[
        {"role": "system", "content": "Extract every factual claim. Rate confidence 0-1."},
        {"role": "user", "content": text},
    ],
)
facts = response.output_parsed.facts if response.output_parsed else []   # None = refusal

# Input:  "Alice manages the infrastructure team."
# facts:  [Fact(subject='Alice', predicate='manages',
#               object='infrastructure team', ...)]`,
      highlights: [
        'The API constrains generation to the schema — no missing keys, no wrong types',
        'Older code used JSON mode (json_object) + schema in the prompt: valid JSON, but not necessarily yours',
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
    type: 'standard',
    content: {
      title: 'From facts to nodes and edges',
      icon: 'git-branch',
      points: [
        'Each validated fact is a triple: **subject → predicate → object**.',
        '**Subject** and **object** become nodes; **predicate** becomes the directed edge.',
        '*Marquez assessed the Meridian reactor* → `Juno Marquez --[assessed]--> Meridian reactor`.',
        'Same name = same node, so facts from different logs **join into one graph**.',
        'Confidence and source text live **on the edge** — every hop stays citable.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'The names are guessed',
      icon: 'alert-triangle',
      points: [
        'Nothing constrains `subject`, `predicate`, or `object` — the model invents the wording.',
        '"Juno Marquez" and "Engineer Marquez" become **two nodes**, and the path between them silently vanishes.',
        'Edge labels drift too ("assessed" / "evaluated"), so you cannot filter on a relation.',
        'Fix: a **controlled vocabulary** — `predicate: Literal["assessed", "repaired", ...]`.',
        'Fix: **canonicalise entity names** before adding them, so aliases collapse to one node.',
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
  // {
  //   type: 'title',
  //   content: {
  //     title: 'Grounded QA',
  //     subtitle: 'Answering questions with graph evidence and citations',
  //     icon: 'help-circle',
  //   },
  // },

  // {
  //   type: 'standard',
  //   content: {
  //     title: 'Grounded QA from the graph',
  //     icon: 'help-circle',
  //     points: [
  //       'Query the graph for relevant entities and relationships.',
  //       'Build a prompt with the **graph evidence** as context.',
  //       'Answer must **cite** which entities/relationships it used.',
  //       'No evidence found → low-confidence answer with a caveat.',
  //     ],
  //   },
  // },
  // {
  //   type: 'comparison',
  //   content: {
  //     title: 'Vector RAG vs graph RAG',
  //     left: {
  //       label: 'Vector RAG',
  //       items: [
  //         'Retrieves text chunks by semantic similarity',
  //         'Good for "what does the doc say about X?"',
  //         'Flat — no relationship structure',
  //         'Simple to build and scale',
  //       ],
  //     },
  //     right: {
  //       label: 'Graph RAG',
  //       items: [
  //         'Traverses entity relationships',
  //         'Good for "how is X related to Y?"',
  //         'Multi-hop reasoning built in',
  //         'Requires extraction pipeline first',
  //       ],
  //     },
  //   },
  // },
  // ---- Demo: Grounded QA ----
  // {
  //   type: 'title',
  //   content: {
  //     title: 'Demo — Grounded QA',
  //     subtitle: 'Switch to terminal: python demo/03_grounded_qa.py',
  //     icon: 'rocket',
  //   },
  // },

  // ---- Section: Graph as a tool ----
  {
    type: 'title',
    content: {
      title: 'The graph as a tool',
      subtitle: 'An MCP server the agent chooses to call',
      icon: 'server',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Let the agent walk the graph',
      icon: 'route',
      points: [
        'Demos 02 and 03 **hard-code** the walk: pick entities, then fetch neighbours.',
        'An MCP server turns those queries into **tools**: list, neighbours, path, facts within N hops.',
        'The agent loop is the one from Module 3. The model picks the tool. Your code runs it.',
        'The server is deterministic. It reads a saved graph — no model call inside the tool.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'One tool, one graph question',
      code: `@server.tool()
def shortest_path(start: str, end: str) -> str:
    """Shortest chain of facts connecting two entities."""
    ...

# The agent sees the tool list, then:
#   list_entities(query="chief engineer")
#   shortest_path(start="Mira Chen", end="osmium")`,
      highlights: [
        'The docstring and the type hints become the schema the model reads',
        'stdio: demo 04 spawns graph_server.py, no second terminal',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Graph agent',
      subtitle: 'Switch to terminal: python demo/04_graph_agent.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Summary and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Summary',
      rules: [
        {
          rule: 'Schema is the contract',
          example:
            'Pydantic structured outputs are what you can validate, store, and query.',
          icon: 'file-text',
        },
        {
          rule: 'Every fact needs provenance and a score',
          example:
            'A fact without a source is an unsupported claim. Confidence decides what you keep.',
          icon: 'link',
        },
        {
          rule: 'Entities and edges make a graph',
          example: 'Multi-hop questions walk relationships, not just similar text.',
          icon: 'git-branch',
        },
        {
          rule: 'Grounded QA cites the source',
          example: 'Answer from stored facts, and show where each one came from.',
          icon: 'book-open',
        },
        {
          rule: 'The graph can be a tool',
          example:
            'An MCP server answers list, neighbours, and path. The agent decides which to call.',
          icon: 'server',
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
