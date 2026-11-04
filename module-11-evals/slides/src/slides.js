export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 11 — Evals',
      subtitle: 'Evaluating your agent',
      icon: 'trending-up',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Catch agent regressions with **golden tests**: frozen reference, exact-match tools, judged prose.',
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
          'You find issues when customers tell you about them',
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
        '**Agent behaviour** — did it call the right tools? Golden tests vs a frozen reference.',
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
      subtitle: 'Compare against known good results',
      icon: 'check-square',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is a golden test?',
      description:
        'A **golden test** compares the output of the agent against a known good result. When you make changes to your agent, you can get a numeric score that tells you if you are still good.',
      icon: 'check-square',
    },
  },
  {
    type: 'code',
    content: {
      title: 'run_case → score_case',
      code: `actual = run_case(client, question)      # what the build did
score_case(actual, case, judge)          # vs the frozen reference

# {"id": "warp-status", "score": 0.25, "passed": False,
#  "criteria": {"tools": 0.00, "correctness": 0.25,
#               "completeness": 0.00, "relevance": 0.75}}`,
      highlights: [
        'Tool calls are structured, so they exact-match: 0 or 1.',
        'LLM-as-judge scores the prose against the reference on criteria such as correctness, completeness, and relevance.',
        'An aggregated score gives a hard numerical value — and the criteria say where it went wrong.',
      ],
    },
  },
  {
    type: 'equation',
    content: {
      title: 'Scoring the suite',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <mi>suite</mi>
  <mo>=</mo>
  <mfrac>
    <mn>1</mn>
    <mi>N</mi>
  </mfrac>
  <munderover>
    <mo>&sum;</mo>
    <mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow>
    <mi>N</mi>
  </munderover>
  <mfrac>
    <mn>1</mn>
    <mi>M</mi>
  </mfrac>
  <munderover>
    <mo>&sum;</mo>
    <mrow><mi>j</mi><mo>=</mo><mn>1</mn></mrow>
    <mi>M</mi>
  </munderover>
  <msub><mi>s</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub>
  <mspace width="1.5em"/>
  <msub><mi>s</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub>
  <mo>&isin;</mo>
  <mo>[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo>]</mo>
</math>`,
      description:
        'Two means. Average the criteria for one case, then average the cases for the suite. A continuous score lets a paraphrase land near 1.',
      points: [
        '**suite** — the score for the whole golden set.',
        '**N** — how many cases. **i** is one of them.',
        '**M** — how many criteria on a case. **j** is one of them: tools, correctness, completeness, relevance.',
        '**s_ij** — case i’s score on criterion j.',
        '**[0, 1]** — 0 is a miss, 1 is perfect, and a value in between is partial credit.',
      ],
      credit:
        'Equal weights give a plain mean; the part 5 scorecard replaces 1/M with weights that sum to 1. Tool calls stay the exact-match criterion — structured, so 0 or 1.',
    },
  },

  // --- 2. Retrieval metrics ---
  {
    type: 'title',
    content: {
      title: '2. RAG Retrieval metrics',
      subtitle: 'Did we fetch the right documents?',
      icon: 'search',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Recall, precision, and MRR',
      icon: 'search',
      points: [
        'Start from a **labelled set**: for each query, the document IDs that should come back.',
        '**Recall@k** is the fraction of gold docs in the top k. Did we miss evidence?',
        '**Precision@k** is the fraction of the top k that are gold. How much junk hit the prompt?',
        '**MRR** (mean reciprocal rank) is `1/rank` of the first relevant hit. How far down was the first good doc?',
      ],
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
      points: [
        '**@** — say "at". Recall@k is recall at k.',
        '**∩** — the intersection: documents in both sets. Say "intersect" or "cap".',
        '**| |** — the size of the set: how many documents are inside.',
        '**top@k** — the first k results. **relevant** — the gold set for that query.',
      ],
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
      credit: 'Reuse this as a release check on a Module 12 capstone.',
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
      title: 'Summary',
      rules: [
        {
          icon: 'zap',
          rule: 'Golden tests freeze the outcome',
          example:
            'The fixture does not script the agent. Exact-match the tool calls; judge the prose.',
        },
        {
          icon: 'search',
          rule: 'Retrieval has numbers',
          example:
            'recall@k, precision@k, and MRR, on a small set you labelled properly.',
        },
        {
          icon: 'scale',
          rule: 'Judge the answer, then check the claims',
          example:
            'Correctness, completeness, relevance — then faithfulness against the retrieved context.',
        },
        {
          icon: 'award',
          rule: 'Compare on a delta, gate on a floor',
          example:
            '“Did we get better?” is a different question from “is this shippable?”',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — five labs',
      points: [
        '01 Golden tests — frozen reference, score tools + answer, run a suite',
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
      subtitle: 'Next: productionisation',
      icon: 'check-circle',
    },
  },
];
