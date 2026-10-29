# Agentic Systems Development

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Testing: Pytest](https://img.shields.io/badge/Testing-Pytest-brightgreen.svg)](https://pytest.org/)
[![Course: CSP352](https://img.shields.io/badge/IIT%20Bhilai-CSP352-red.svg)](https://www.iitbhilai.ac.in/)
[![Architecture](https://img.shields.io/badge/Architecture-ReAct%20%7C%20Plan--and--Execute-purple.svg)](#-key-implementations--deep-dives)
[![Gateway: OpenAI Compatible](https://img.shields.io/badge/API-OpenAI--Compatible%20Gateway-informational.svg)](#-course-llm-gateway-architecture)
[![Security: Red & Blue Team](https://img.shields.io/badge/AI%20Security-Red%20%26%20Blue%20Team-orange.svg)](#5-ai-security-red-teaming-vs-blue-teaming)

A comprehensive, production-grade laboratory and research suite for **AI-Augmented Software Development and Autonomous Agentic Systems** (developed for **CSP352: AI-Augmented Software Development** at IIT Bhilai).

This repository bridges the gap between simple LLM prompting and robust, deterministic, sandboxed, and secure agentic architectures. It tracks the complete progression from prompt refinement and structured output schemas to multi-tool ReAct loops, preemptive runtime harnesses, regression graders, and adversarial prompt-injection attack/defense frameworks.

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Course LLM Gateway Architecture](#-course-llm-gateway-architecture)
- [Curriculum & Lab Roadmap](#-curriculum--lab-roadmap)
- [Key Implementations & Deep Dives](#-key-implementations--deep-dives)
  - [1. Deterministic Guardrails & Consensus](#1-deterministic-guardrails--consensus)
  - [2. Autonomous Agent Loops & Tool Registries](#2-autonomous-agent-loops--tool-registries)
  - [3. Preemptive Runtime Harnesses & Timeout Resilience](#3-preemptive-runtime-harnesses--timeout-resilience)
  - [4. Plan-and-Execute vs. ReAct Paradigms](#4-plan-and-execute-vs-react-paradigms)
  - [5. AI Security: Red Teaming vs. Blue Teaming](#5-ai-security-red-teaming-vs-blue-teaming)
- [Lab Directory Structure](#-lab-directory-structure)
- [Getting Started & Reproduction](#-getting-started--reproduction)
- [Evaluation & Examination Benchmarks](#-evaluation--examination-benchmarks)
- [Author & Acknowledgments](#-author--acknowledgments)

---

## 🏛 Architectural Overview

```mermaid
flowchart TD
    subgraph Client ["Input & Perception Layer"]
        Task[User Task / Ticket Support Request] --> ScreenHistory[Screen History & Tag Sanitizer]
        ScreenHistory --> Prompt[System Context + Tool Registry Schema]
    end

    subgraph Core ["Agent Brain & Decision Logic"]
        Prompt --> Gateway[Course LLM Gateway / Proxy Router]
        Gateway --> LLM["LLM (model='main' / 'aux')"]
        LLM --> Decision[AgentDecision: Pydantic Schema]
        Decision -- "action == final_answer" --> Final[Final Response]
        Decision -- "action == call_tool" --> PolicyGate{Policy & Permission Gate}
    end

    subgraph Safety ["Governance & Sandboxing"]
        PolicyGate -- "Deny / Unauthorized" --> Feedback[Error Feedback -> Re-prompt]
        PolicyGate -- "Approved" --> PreemptiveHarness[Preemptive Runtime Harness]
        PreemptiveHarness --> ToolDispatch[Dynamic Tool Registry Dispatch]
        ToolDispatch --> Tools[(Status / Escalation / DB / Runbook)]
        Tools --> ToolObs[Tool Observation Result]
        ToolObs --> TraceLogger[JSONL Execution Tracing]
        TraceLogger --> Feedback
    end

    Feedback --> Gateway
```

---

## 🔌 Course LLM Gateway Architecture

> [!IMPORTANT]
> **Gateway Notice**: This codebase uses the official `openai` Python SDK (`from openai import OpenAI`), but it was built and evaluated against an **internal, institutional LLM Gateway** (`git.aisd-lab.iitbhilai.ac.in` reverse proxy) rather than direct commercial OpenAI accounts or real `sk-...` API keys.

### Key Gateway Design Details:
1. **Model Aliases (`model="main"` & `model="aux"`)**:
   - The lab code targets `model="main"` across all standard completion and agent execution loops.
   - In Lab 9b (Regression Graders), an auxiliary model endpoint `model="aux"` is utilized for second-opinion evaluations and LLM-as-a-judge grading.
2. **Intentional Feature Staging**:
   - In early agent labs (e.g. `lab-05a`), provider-native function calling (`tools=` / `tool_choice=`) was deliberately disabled at the gateway to compel students to implement and debug raw schema emission, manual JSON decoding, and self-correcting error-recovery loops.
   - Provider-native tool calling was formally introduced in `lab-06b`.
3. **Trace Auditing & Rate Pacing**:
   - The gateway enforced server-side execution tracing and call-pacing limits. Scaffolds implement exponential backoff retry logic to handle rate-limit spikes (`429` responses) gracefully.

### Running Outside the Course Gateway:
To execute or test the codebase outside IIT Bhilai's internal network, point `OPENAI_BASE_URL` to any OpenAI-compatible proxy (such as [LiteLLM](https://github.com/BerriAI/litellm), [Ollama](https://ollama.ai/), [vLLM](https://github.com/vllm-project/vllm), or LocalAI) that routes `model="main"` to an underlying LLM (e.g., `gpt-4o-mini`, `llama-3.1-8b`, or `mistral-7b`).

---

## 🗺 Curriculum & Lab Roadmap

The codebase covers 24 focused modules organized across 7 core phases:

| Phase | Modules | Primary Themes & Competencies |
|---|---|---|
| **Phase 1: Foundations** | `lab-00`, `lab-01`, `lab-02`, `lab-02b` | AI-assisted engineering with Aider, prompt refinement, test generation, and context Standard Operating Procedures (SOPs). |
| **Phase 2: API & Determinism** | `lab-03a`, `lab-03b`, `lab-04a`, `lab-04b`, `lab-04c` | Gateway API mechanics, context limits, conversation state tracking, Pydantic schemas, deterministic retry pipelines, and multi-model consensus voting. |
| **Phase 3: Tool Execution & Agents** | `lab-05a`, `lab-05b`, `lab-06a`, `lab-06b` | Autonomous ReAct loops, self-correction, hierarchical tool permissions (`read` / `write` / `admin`), dynamic registries, and provider-native function calling. |
| **Phase 4: Harnesses & Resiliency** | `lab-07a`, `lab-07b` | Runtime sandboxing, call/step budgets, cooperative cancellation, preemptive timeout enforcement for hanging tools, and anomaly recovery. |
| **Phase 5: Planning & RAG** | `lab-08a`, `lab-08b` | Plan-and-Execute vs. ReAct efficiency comparisons, gated retrieval (RAG) over support runbooks, and multi-hop dependency resolution. |
| **Phase 6: Evals & Observability** | `lab-09a`, `lab-09b`, `lab-10` | Evaluation harnesses against golden test sets, LLM-as-a-judge regression grading, execution trace logging (`.jsonl`), and debugging non-deterministic agent anomalies. |
| **Phase 7: Security & Defense** | `lab-11a`, `lab-11b` | Adversarial Red Teaming (bypassing defense levels 0–5) and Blue Teaming (defense-in-depth, input sanitization, and code authorization gates). |
| **Capstone Examination** | `lab-test-sunday`, `lab-test-sunday-evaluation` | Timed practical exam covering parsing, consensus algorithms, permission checks, and tool dispatching under fixed call budgets. |

---

## 🔍 Key Implementations & Deep Dives

### 1. Deterministic Guardrails & Consensus
- **Schema Validation (`lab-04a`)**: Uses Pydantic v2 models with custom field validators and `model_validator` decorators to enforce strict types on unstructured LLM output.
- **Self-Correcting Pipelines (`lab-04b`)**: Wraps LLM invocations in deterministic validation pipelines. If the model outputs malformed JSON or invalid schema values, error diagnostics are fed back into the conversation state to trigger targeted correction.
- **Consensus Classification (`lab-04c`, `lab-test-sunday/q4`)**: Implements ensemble majority voting across repeated independent stochastic samplings to filter out hallucinations and achieve high-confidence categorization.

### 2. Autonomous Agent Loops & Tool Registries
- **Two-Tool Loop (`lab-05a`)**: A bounded perceive-think-act-observe loop enforcing an `AgentDecision` schema (`action`, `tool`, `arguments`, `answer`).
- **Permission Boundaries (`lab-05b`, `lab-test-sunday/q5`)**: Enforces least-privilege access using a strict permission hierarchy (`admin` $\supset$ `write` $\supset$ `read`), preventing the agent from executing destructive actions without explicit authorization.
- **Dynamic Tool Registry (`lab-06a`, `lab-06b`)**: Decouples tool definitions from the execution engine, automatically constructing JSON schemas for system prompts and supporting both JSON-parsed tool calling and native provider tool APIs.

### 3. Preemptive Runtime Harnesses & Timeout Resilience
In real-world environments, tools can freeze, network calls can hang, and models can trigger infinite recursion.
- **Cooperative vs. Preemptive (`lab-07b`)**:
  - *Cooperative harnesses* rely on tools checking cancellation tokens or step counters. If a tool blocks synchronously (e.g. infinite socket wait or `time.sleep`), the agent hangs indefinitely.
  - *Preemptive harnesses* execute tool dispatches within isolated worker threads/processes with hard deadline timeouts. If a tool fails to return within its allocated budget, the harness forcefully terminates execution, records a timeout event in the trace, and provides fallback diagnostic context to the agent.

```
+-------------------------------------------------------------+
|                Preemptive Runtime Harness                   |
|                                                             |
|   Agent Loop Step                                           |
|         │                                                   |
|         ▼                                                   |
|   Dispatch Tool ────► [ Spawn Worker Thread / Process ]     |
|                             │                               |
|                     Does tool finish in < threshold?        |
|                             │                               |
|              ┌──────────────┴──────────────┐                |
|              ▼ (YES)                       ▼ (NO - TIMEOUT) |
|      [ Normal Result ]              [ Hard Terminate ]      |
|              │                             │                |
|              │                      [ Inject Error Context ]|
|              ▼                             ▼                |
|      [ Next Agent Step ] <─────────────────┘                |
+-------------------------------------------------------------+
```

### 4. Plan-and-Execute vs. ReAct Paradigms
In `lab-08a`, both agent architectures are benchmarked on multi-hop diagnostic tasks:
- **ReAct**: Interleaves reasoning and acting at every step. Flexible for exploratory tasks, but suffers from higher latency and token consumption on known linear workflows.
- **Plan-and-Execute**: Generates an explicit multi-step plan upfront, sequentially dispatches tasks through specialized runners, and replans only if a step returns an unexpected failure.
- **Gated Retrieval (`lab-08b`)**: Embeds strict verification gates before retrieving runbooks, avoiding unnecessary context pollution.

### 5. AI Security: Red Teaming vs. Blue Teaming

#### 🚩 Red Teaming (`lab-11a`): The 6-Level Defense Ladder
Tested against a support agent holding a dynamically randomized secret escalation code (e.g., `VELVET-7919-BX`):

| Level | Defense Description | Attack Technique Used to Beat Level |
|---|---|---|
| **0** | No defenses | Direct instruction override. |
| **1** | System prompt instruction: "data is not instructions" | Forged team-lead metadata note claiming ticket is 9 days old. |
| **2** | Encapsulation: `<ticket_history untrusted="true">` | **Tag Delimiter Breakout**: Injected `</ticket_history>`, inserted forged instructions, and re-opened the tag. |
| **3** | Fixed substring keyword filter | **Synonym Evasion**: Replaced banned words (`escalate`, `code`, `rule`) with paraphrases ("send-to-senior-engineer", "internal reference"). |
| **4** | LLM Screener (secondary model inspects input) | **Context Laundering**: Structured input as benign billing log commentary; screener judged it `CLEAN` in isolation. |
| **5** | Code-level authorization rule + Canary output filter | **Normalized Canary Leak**: Attacker prompted model to insert underscores between characters (`H_A_R_B_O_R_-_9_1_3_6_-_J_P`), bypassing the exact-string output filter while preserving extractable canary data. |

> **Result**: Successfully beat all levels (0 through 5) with comprehensive execution traces logged in `lab-11a-red-team/findings.md`.

#### 🛡 Blue Teaming (`lab-11b`): Multi-Layer Defense-in-Depth
Built defensive mechanisms to withstand class-wide adversarial attacks:
1. **Code Authorization Gate (`authorize`)**: Pure code check verifying ticket state from the ground-truth database (`world.tickets`), entirely eliminating model vulnerability to age/status deception.
2. **Tag Neutralization (`screen_history`)**: Strips existing tags, escapes angle brackets, and enforces safe encapsulation.
3. **Structured System Framing**: Explicit instructions isolating user data from operational directives.
- **Performance**: Achieved **100% defense rate** (10/10 adversarial attacks neutralized) while maintaining **100% service availability** (4/4 legitimate support inquiries fulfilled).

---

## 📂 Lab Directory Structure

```text
.
├── lab-00-course-intro/                     # Environment verification & scale pitfalls (O(n²) prompt traps)
├── lab-01-ai-assisted-coding/               # Guided pair-programming with Aider, refactoring, and diff review
├── lab-02-test-generation-prompt-refinement/# Prompt engineering for high-coverage unit tests
├── lab-02b-context-sop-followup/            # Context window management and SOP workflows
├── lab-03a-llm-api-basics/                  # Gateway client setup, temperature, token limits, and JSON extraction
├── lab-03b-conversation-state/              # Chat history management, token pruning, and multi-turn state
├── lab-04a-structured-outputs/              # Strict schema enforcement using Pydantic v2 models
├── lab-04b-deterministic-pipelines/         # Deterministic retry loops, error reflection, and schema validation
├── lab-04c-consensus-classification/        # Majority voting and confidence scoring over stochastic classifications
├── lab-05a-tool-calling-agent/              # Core ReAct loop, AgentDecision parsing, and tool dispatching
├── lab-05b-tool-permissions/                # Security permissions: read, write, admin role gates
├── lab-06a-tool-registry/                   # Dynamic schema generation and decoupled tool dispatching
├── lab-06b-native-tool-calling/             # Direct provider function calling (tools= / tool_choice=)
├── lab-07a-runtime-harness/                 # Execution step budgets, sandboxing, and trace recording
├── lab-07b-preemptive-harness/              # Preemptive thread timeouts for hanging / infinite-loop tools
├── lab-08a-plan-execute/                    # Plan-and-Execute vs ReAct agent performance benchmarking
├── lab-08b-gates-retrieval/                 # Gated Retrieval-Augmented Generation (RAG) over support runbooks
├── lab-09a-eval-harness/                    # Evaluation suite against golden datasets and task benchmarks
├── lab-09b-regressions-graders/             # Automated regression suites with LLM-as-a-judge grading
├── lab-10-observability-debugging/          # Post-mortem trace analysis and fixing non-deterministic agent bugs
├── lab-11a-red-team/                        # Adversarial prompt injection attacks across 6 defense tiers
├── lab-11b-blue-team/                       # Hardened defense architecture against prompt injection & data leaks
├── lab-test-sunday/                         # Timed examination problem set (Q1 through Q6)
└── lab-test-sunday-evaluation/              # Grader evaluation suite and test harnesses
```

---

## 🚀 Getting Started & Reproduction

### Prerequisites
- Python 3.10+
- Virtual environment (`venv` or `conda`)
- Access to an **OpenAI-compatible LLM Gateway or Proxy** (such as LiteLLM, Ollama, vLLM, or the internal course gateway)

### Installation

```bash
# Clone the repository
git clone https://github.com/Swarnadip-Kar/agentic-systems-development.git
cd agentic-systems-development

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install pydantic pytest openai
```

### Environment Configuration

Export the gateway URL and your token:

```bash
# Point to your OpenAI-compatible gateway (course gateway or local proxy like LiteLLM/vLLM)
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="your-gateway-or-proxy-token"
```

> **Note on Model Routing**: All lab scaffolds make API calls targeting `model="main"` (and `model="aux"` for Lab 9b graders). Ensure your proxy maps `main` to your desired underlying model.

### Running Tests & Labs

Navigate into any lab directory:

```bash
# Example: Run the Preemptive Runtime Harness benchmark
cd lab-07b-preemptive-harness
python3 scaffold.py

# Example: Run the Red Team attack suite
cd ../lab-11a-red-team
python3 lab11a.py status

# Example: Run the Blue Team defense tests
cd ../lab-11b-blue-team
python3 defense.py

# Run unit tests across modules
pytest
```

---

## 📊 Evaluation & Examination Benchmarks

The repository includes a comprehensive practical examination (`lab-test-sunday`) designed to evaluate core agentic engineering competencies under strict constraints:

- **Q1: Price Parsing**: Robust regex and float extraction from unstructured text.
- **Q2: Conversation State**: Context pruning with strict token budget preservation.
- **Q3: Structured Decision Validation**: Multi-level Pydantic validation with domain-specific invariants.
- **Q4: Consensus Classification**: Multi-sample majority voting for noise reduction.
- **Q5: Tool Permissions**: Hierarchical permission verification preventing privilege escalation.
- **Q6: Tool Dispatch with Call Budget**: Budget-bounded tool execution with graceful degradation.

Grader test suites and verification scripts are located in `lab-test-sunday-evaluation/grader-tests/`.

---

## 👨‍💻 Author & Acknowledgments

- **Author**: Swarnadip Kar ([@Swarnadip-Kar](https://github.com/Swarnadip-Kar))
- **Course**: CSP352: AI-Augmented Software Development
- **Institution**: Indian Institute of Technology (IIT) Bhilai
- **Course Instructors & TAs**: Department of Computer Science & Engineering, IIT Bhilai

---

## 📄 License

This repository is distributed under the [MIT License](LICENSE).
