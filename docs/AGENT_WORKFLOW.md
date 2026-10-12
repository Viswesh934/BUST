# BUST — Agent Workflow & Demo Video Guide

> **Visual Workflow Diagrams, Architecture Deep-Dive, and 2-Minute Demo Video Script**  
> Tailored for presenting **BUST** at hackathon demo days, investor pitches, and partner evaluations (**NeatLogs**, **Entire**, and **cfo.ai**).

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph UI ["1. Sales Workspace Frontend (Astro + Tailwind)"]
        User["Sales Rep / AE Input\n('Close $300k ACME deal vs Datadog...')"]
        Dashboard["Interactive Deal Workspace\n• 3D Battlecard Flip Cards\n• PPT Slide Filmstrip Viewer\n• Mermaid Closing Transit Map\n• Stakeholder Social Graph"]
        DealRoom["Encrypted Buyer Deal Room\n(Public Keycard Share Link)"]
    end

    subgraph API ["2. Lambda Serverless Gateway (AWS)"]
        FastAPI["FastAPI Backend\n(Mangum Handler)"]
    end

    subgraph Orchestrator ["3. Autonomous Sales Agent Orchestrator"]
        State["Deal State & Memory Tracker\n(Stage • Health • Objections • Risks)"]
        CFO["cfo.ai Financial Engine\n(ARR • Payback • ROI Multiple • Tier)"]
        Grounding["Technical Grounding Engine\n(GitHub • Docs • PDFs)"]
        LLM["Tactical Decision Engine\n(LiteLLM: nova-pro / claude-sonnet-4.6)"]
    end

    subgraph DAG ["4. Directed Acyclic Graph (DAG) Execution Engine"]
        Formulation["DAG Dependency Graph Formulation"]
        ParallelExec["Concurrent Parallel Tool Execution\n(asyncio.gather with self-healing retries)"]
    end

    subgraph Tools ["5. Deterministic Sales Tools"]
        T_BC["create_battlecards\n(Objection Talk-Tracks)"]
        T_PPT["create_presentation\n(4-Slide 16:9 Deck)"]
        T_MAP["create_flowchart\n(Mutual Action Plan)"]
        T_EMAIL["create_email\n(Executive Proposal)"]
        T_COMP["analyze_competitor\n(Crustdata Deep Research)"]
        T_SUITE["publish_suite\n(Digital Keycard)"]
    end

    subgraph Storage ["6. Persistence & Observability"]
        SQLite[("SQLite Deal Store\n(Persistent Artifacts)")]
        NeatLogs["NeatLogs Telemetry\n(LLM Tracing & Tool Spans)"]
        Entire["Entire Git Checkpoints\n(Versioned Agent State)"]
    end

    User --> FastAPI
    FastAPI --> Orchestrator
    State --> LLM
    CFO --> LLM
    Grounding --> LLM
    LLM --> DAG
    Formulation --> ParallelExec
    ParallelExec --> T_BC & T_PPT & T_MAP & T_EMAIL & T_COMP & T_SUITE
    Tools --> SQLite
    Tools -.-> NeatLogs
    Orchestrator -.-> Entire
    SQLite --> Dashboard
    SQLite --> DealRoom
```

---

## 2. The 5-Stage Agent Lifecycle (Step-by-Step Flow)

```mermaid
sequenceDiagram
    autonumber
    actor AE as Sales Rep (AE)
    participant UI as Astro Workspace UI
    participant Orch as Agent Orchestrator
    participant CFO as cfo.ai MCP Engine
    participant Ground as Technical Grounding
    participant LLM as LiteLLM (AI Gateway)
    participant DAG as Sales DAG Engine
    participant Neat as NeatLogs Ingest
    participant Store as SQLite Artifact Store

    AE->>UI: Inputs deal goal & meeting notes
    UI->>Orch: POST /api/agent/run
    
    rect rgb(240, 248, 255)
        Note over Orch,Ground: Phase 1: Context Hydration & Grounding
        Orch->>Store: Query existing collateral for account
        Orch->>CFO: Calculate contract ARR, labor savings & payback days
        CFO-->>Orch: Financial context (e.g. 42-day payback, 1.8x ROI)
        Orch->>Ground: Retrieve verified technical facts from repos/PDFs
    end

    rect rgb(255, 250, 240)
        Note over Orch,LLM: Phase 2: Autonomous Tactical Decision
        Orch->>LLM: Synthesize state prompt + history + cfo.ai metrics
        LLM->>Neat: Trace prompt tokens & latency span (neatlogs.wrap)
        LLM-->>Orch: Returns tactical plan (decisions, rationale, tailored briefs)
    end

    rect rgb(245, 255, 250)
        Note over Orch,DAG: Phase 3: DAG Formulation & Parallel Execution
        Orch->>DAG: Build execution graph with topological dependencies
        par Concurrent Tool Execution
            DAG->>DAG: Execute create_battlecards
            DAG->>DAG: Execute create_presentation
            DAG->>DAG: Execute analyze_competitor (Crustdata)
            DAG->>DAG: Execute create_flowchart (Mermaid)
        end
        DAG->>Neat: Record node execution spans (@neatlogs.span)
        DAG->>Store: Persist deliverable envelopes into SQLite
    end

    DAG-->>UI: Return synthesized advisory + structured deliverables
    UI-->>AE: Live UI updates: slides, battlecards, flowchart, and deal room keycard
```

---

## 3. Autonomous Sales DAG Engine: Parallel Dependency Graph

When the agent decides which deliverables to build, it doesn't run a slow, brittle sequential loop. It builds an autonomous **Directed Acyclic Graph (DAG)**:

```mermaid
graph TD
    classDef pending fill:#e2e8f0,stroke:#64748b,stroke-width:2px;
    classDef running fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
    classDef done fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;

    Start(["User Directive: Close $300k ACME Deal"]):::done --> Node0["0. Tactical Decision Engine\n(Synthesizes tool briefs & CFO context)"]:::done

    Node0 --> Node1["1. Competitor Teardown\n(Crustdata firmographics & revenue)"]:::done
    Node0 --> Node2["2. Objection Battlecards\n(Talk-tracks & TCO differentiators)"]:::done
    Node0 --> Node3["3. Mutual Action Plan\n(6-stage Mermaid roadmap)"]:::done

    Node1 -.->|"Pipelines pricing traps"| Node4["4. Executive Pitch Deck\n(16:9 widescreen presentation)"]:::done
    Node2 -.->|"Pipelines talk-tracks"| Node4
    Node0 --> Node4

    Node4 --> Node5["5. Executive Follow-Up Email\n(CFO savings & deck recap)"]:::done
    Node0 --> Node6["6. Public Buyer Deal Room\n(Publish encrypted share suite)"]:::done

    Node5 --> Finish(["Complete Deal Collateral Package Ready"]):::done
    Node6 --> Finish
```

---

## 4. 2-Minute Demo Video Script & Storyboard

Use this exact script and timing for your video presentation:

| Timestamp | Visual on Screen | Voiceover Script (What to Say) |
| :--- | :--- | :--- |
| **0:00 – 0:20**<br>*(The Problem)* | Show messy Google Drive / desktop folders with separate pitch decks, docs, and notes. Then open **BUST** (`bust-omega.vercel.app`). | *"Enterprise account executives spend over 30% of their week manually prepping deal collateral—drafting follow-ups, hunting down competitor data, and tailoring decks. Existing AI chatbots generate generic text snippets, but don't manage the real workflow of building, editing, and sharing deal-winning collateral. Meet **BUST**: One deal instruction, multiple sales deliverables."* |
| **0:20 – 0:45**<br>*(The Live Prompt & Agent)* | Type into BUST Chat: `Close a $300k ARR deal with ACME Corp against Datadog. CTO raised pricing and data residency concerns. Build battlecards, an executive deck, and a mutual action plan.` Hit Enter. | *"I simply tell BUST the deal goal and prospect objections. Immediately, our autonomous multi-turn agent kicks off. Instead of running a generic prompt, BUST queries our database for existing account context, pulls live financial metrics from **cfo.ai**, and formulates a Directed Acyclic Graph to execute deterministic tools in parallel."* |
| **0:45 – 1:10**<br>*(Deliverables Tour)* | Click through the generated tabs in BUST:<br>1. **Battlecards** (flip a card).<br>2. **Pitch Deck** (cycle slides).<br>3. **Mutual Action Plan**.<br>4. **Competitor** (Datadog revenue & Crustdata). | *"In seconds, BUST delivers an entire deal suite: **Objection Battlecards** with 3D flip cards for rapid AE pitch practice; a **4-slide 16:9 Executive Pitch Deck** grounded in verified technical citations; a visual **Mutual Action Plan** with milestone dates; and deep competitor intelligence powered by **Crustdata**."* |
| **1:10 – 1:35**<br>*(Partners: NeatLogs, Entire, cfo.ai)* | Quickly show:<br>1. **NeatLogs Dashboard** / Trace.<br>2. **Entire Session Link**.<br>3. Slide 4 highlighting **cfo.ai ROI numbers**. | *"Under the hood, three core technologies power BUST:<br>• **NeatLogs** provides end-to-end observability, tracing every LLM turn and tool span to resolve latency bottlenecks.<br>• **Entire** tracks our agent development checkpoints across git history, giving us verifiable prompt improvement.<br>• And **cfo.ai** plans our business unit economics while dynamically grounding every deliverable in real contract ARR, labor savings, and payback metrics."* |
| **1:35 – 2:00**<br>*(Buyer Deal Room & Outro)* | Click **Publish Deal Room**, show the generated public link (`/api/public/suites/:id`) opening in a guest window. | *"Finally, with one click, BUST publishes a passwordless, encrypted Buyer Deal Room for the prospect champion to share internally with their CFO. That's BUST—turning deal notes into closed enterprise contracts in seconds."* |

---

## 5. Key Highlights to Emphasize in the Presentation
1. **Not Just a Chatbot**: An autonomous decision engine that formulates a **DAG of deterministic tools**, pipelines context between nodes, and self-heals retries.
2. **Deep Observability with NeatLogs**: Real production telemetry (`workflow: llm-completion`) tracing prompt tokens, tool latencies, and automated incident recovery.
3. **Verifiable Development with Entire**: 11+ git checkpoints recorded with immutable Entire hashes ([Live Entire Session](https://entire.io/gh/Viswesh934/BUST/session/77ad5304-ab6c-4459-bb55-06cdea62fa7f)).
4. **Financial Grounding with cfo.ai**: Enterprise deals close on ROI; BUST embeds verified payback periods directly into customer-facing slides.
