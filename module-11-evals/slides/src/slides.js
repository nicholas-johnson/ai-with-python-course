export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 11 — Evals',
      subtitle: 'Measure the agent, then ship it',
      icon: 'trending-up',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Regression-test a tool-calling agent with **golden files** and a mock LLM.',
        'Score retrieval with **recall@k**, **precision@k**, and **MRR**.',
        'Grade answers with an **LLM-as-judge** (correctness, completeness, relevance).',
        'Measure **faithfulness**: every claim grounded in retrieved context.',
        '**Compare** two configs and **gate** a release below a floor.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'A live demo is not an eval',
      left: {
        label: 'One chat',
        items: [
          'Sample size: 1',
          'Model drift hides behind “it worked on stage”',
          'No number to compare chunk sizes',
          'You find regressions when crew complain',
        ],
      },
      right: {
        label: 'A frozen test set',
        items: [
          'Same questions after every change',
          'Cheap checks in CI; token spend on a schedule',
          'A vs B on recall, judge, faithfulness',
          'Fail the build when a floor is missed',
        ],
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Five layers',
      icon: 'layers',
      points: [
        '**Agent behaviour** — did it call the right tools? Golden tests.',
        '**Retrieval** — did we fetch the right logs? Recall, precision, MRR.',
        '**Generation** — is the answer good? LLM-as-judge.',
        '**Grounding** — did it invent facts? Faithfulness.',
        '**Release** — is this config better, and good enough? Scorecard + gate.',
      ],
    },
  },

  // --- 1. Golden tests ---
  {
    type: 'title',
    content: {
      title: '1. Golden tests',
      subtitle: 'Mock the model, run the real loop',
      icon: 'check-square',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is a golden test?',
      description:
        'A **golden-file test** freezes one agent conversation. You mock the LLM with scripted `function_call` items and a final text answer string, run the **real** agent loop (handlers still execute), and assert the tools and the answer. Used in CI because it is fast, free, and deterministic — it catches “we stopped calling `get_ship_status`”, not “the prose got slightly worse”.',
      icon: 'check-square',
      credit:
        'Same pattern as the Module 2 eval harness — now a graded lab.',
    },
  },
  {
    type: 'code',
    content: {
      title: 'run_case → score_case',
      code: `actual = run_case(client, case)
# {"tools": [{"name": "get_crew_count",
#             "arguments": {"department": "engineering"}}],
#  "answer": "Engineering has 2 crew members."}

score_case(actual, case)
# {"id": "crew-count-engineering", "passed": True, "mismatches": []}`,
      highlights: [
        'Script the model; execute real handlers.',
        'Exact match on tool names, arguments, and answer.',
        'No API key in pytest.',
      ],
    },
  },

  // --- 2. Retrieval metrics ---
  {
    type: 'title',
    content: {
      title: '2. Retrieval metrics',
      subtitle: 'Did we fetch the right documents?',
      icon: 'search',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What do recall, precision, and MRR measure?',
      description:
        'You need a **labelled set**: for each query, the document IDs that should come back. **Recall@k** is the fraction of those gold docs in the top k (did we miss evidence?). **Precision@k** is the fraction of the top k that are gold (how much junk hit the prompt?). **MRR** is 1/rank of the first relevant hit. Pure functions — no embeddings, no API.',
      icon: 'search',
      credit: 'Classic IR / TREC metrics. Label twenty queries well rather than two hundred guessed ones.',
    },
  },
  {
    type: 'equation',
    content: {
      title: 'Recall@k and Precision@k',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <mi>Recall</mi><mo>@</mo><mi>k</mi>
  <mo>=</mo>
  <mfrac>
    <mrow><mo>|</mo><mi>top</mi><mo>@</mo><mi>k</mi><mo>&#x2229;</mo><mi>relevant</mi><mo>|</mo></mrow>
    <mrow><mo>|</mo><mi>relevant</mi><mo>|</mo></mrow>
  </mfrac>
  <mspace width="2em"/>
  <mi>Precision</mi><mo>@</mo><mi>k</mi>
  <mo>=</mo>
  <mfrac>
    <mrow><mo>|</mo><mi>top</mi><mo>@</mo><mi>k</mi><mo>&#x2229;</mo><mi>relevant</mi><mo>|</mo></mrow>
    <mi>k</mi>
  </mfrac>
</math>`,
      description:
        'Precision divides by k even if fewer than k docs were returned. MRR = 1 / rank of the first relevant document (0 if none).',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Same query, two rankings',
      code: `gold = ["LOG-002", "LOG-011"]
naive  = ["LOG-007", "LOG-016", "LOG-002"]
rerank = ["LOG-002", "LOG-011", "LOG-007"]

# naive   recall@3=0.50  prec@3=0.33  MRR=0.33
# rerank  recall@3=1.00  prec@3=0.67  MRR=1.00`,
      highlights: [
        'Re-run the labelled set after every chunking or index change.',
        'Rerank should move gold docs up — the numbers say whether it did.',
      ],
    },
  },

  // --- 3. LLM-as-judge ---
  {
    type: 'title',
    content: {
      title: '3. LLM-as-judge',
      subtitle: 'Score meaning, not word overlap',
      icon: 'scale',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is LLM-as-judge?',
      description:
        '**LLM-as-judge** asks a strong model to grade a candidate answer against a reference. BLEU and ROUGE count tokens and punish paraphrase (“3500K” vs “3500 Kelvin”). The judge scores **correctness**, **completeness**, and **relevance** from 1–5 and returns JSON. Used to compare prompts and retrieval configs on a frozen set of 20–100 triples.',
      icon: 'scale',
      credit:
        'Zheng et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." arXiv:2306.05685',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Judge prompt → typed scores',
      code: `class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    explanation: str

response = client.responses.parse(
    model=MODEL, text_format=JudgeScores, input=[...])
# JudgeScores(correctness=5, completeness=2, relevance=5,
#             explanation="Only one of three causes.")`,
      highlights: [
        'Temperature 0. The schema rules out missing or out-of-range scores.',
        'Refusal (parsed is None) → scores of 1, do not crash the suite.',
        'Treat scores as relative (A vs B), not absolute truth.',
      ],
    },
  },

  // --- 4. Faithfulness ---
  {
    type: 'title',
    content: {
      title: '4. Faithfulness',
      subtitle: 'Grounded in the sources, not the gold answer',
      icon: 'shield',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is faithfulness?',
      description:
        'A **faithfulness** check splits the answer into claims and asks whether each one is supported by the **retrieved context** — not by a reference answer. An answer can agree with the gold text and still invent a 9000K core temperature. The score is supported_claims / total_claims. Cousin of citation verification; here you want a **ratio** that sits on a scorecard.',
      icon: 'shield',
      credit:
        'Min et al. (2023). "FActScore: Fine-grained Atomic Evaluation of Factual Precision." arXiv:2305.14251',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Claims vs context',
      code: `answer  = "Warp core at 94%. Core temperature is 9000K."
context = "Warp core operating at 94% efficiency. Conduit 7-B fluctuation."

# Claim 1  94%          → supported
# Claim 2  9000K        → unsupported
# faithfulness = 1/2 = 0.5`,
      highlights: [
        'Zero claims → 1.0 (nothing to hallucinate).',
        'Check “unsupported” before “supported” — the first word contains the second.',
      ],
    },
  },

  // --- 5. Scorecard + gate ---
  {
    type: 'title',
    content: {
      title: '5. Scorecard and gate',
      subtitle: 'Which config wins — and is it good enough?',
      icon: 'award',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is a release gate?',
      description:
        'A **scorecard** is retrieval + judge + faithfulness for one pipeline (`rag` vs `rag_rerank`). **Compare** ranks configs on a metric. A **gate** is a floor: if recall drops below 0.6, the build fails even if the demo looked fine. Compare on a delta (“did we get better?”). Gate on a floor (“is this shippable?”).',
      icon: 'award',
      credit: 'Reuse this as a release check on the Module 12 capstone.',
    },
  },
  {
    type: 'code',
    content: {
      title: 'overall + gate',
      code: `judge_norm = (correctness + completeness + relevance) / 15
overall = 0.35*recall + 0.35*judge_norm + 0.30*faithfulness

gate(scorecard, {"avg_recall": 0.6, "overall": 0.55})
# {"passed": False,
#  "failures": [{"metric": "avg_recall", "value": 0.4, "threshold": 0.6}]}`,
      highlights: [
        'Equal to the threshold passes; strictly below fails.',
        'Precision and MRR stay on the card; overall uses recall + judge + faith.',
      ],
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules',
      rules: [
        {
          icon: 'zap',
          rule: 'Mock for CI',
          example: 'Golden tests and retrieval metrics on every commit.',
        },
        {
          icon: 'timer',
          rule: 'Judge on a schedule',
          example: 'Token spend when prompts or retrieval change, not every save.',
        },
        {
          icon: 'file-text',
          rule: 'Label a small set well',
          example: 'Twenty real relevant doc IDs beat two hundred guessed ones.',
        },
        {
          icon: 'eye',
          rule: 'Read the mismatches',
          example: 'Never trust a single average — inspect unsupported claims.',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — five labs',
      points: [
        '01 Golden tests — mock LLM, score tools + answer, run a suite',
        '02 Retrieval metrics — recall@k, precision@k, MRR on ship logs',
        '03 LLM-as-judge — correctness, completeness, relevance',
        '04 Faithfulness — claims vs retrieved context',
        '05 Eval compare — scorecard, winner, release gate',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 11 — Complete',
      subtitle: 'Next: productionisation and the capstone',
      icon: 'check-circle',
    },
  },
];
