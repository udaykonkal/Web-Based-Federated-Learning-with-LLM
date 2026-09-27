# Product Requirements Document (PRD): Federated Learning Collaboration Platform

**Document Version:** 2.0 (Architecturally Aligned & Production Ready)  
**Status:** Approved for Implementation  
**Product Area:** Federated Machine Learning / Distributed AI / Healthcare Consortia  
**Last Updated:** September 2026  
**Reference Implementations:** FastAPI Backend (54/54 Pytest Pass), PyTorch FL Engine, React 18 + Vite + TypeScript Frontend  

---

## 1. Executive Summary & Vision

### 1.1 The Problem
Training high-accuracy, generalized machine learning models in sensitive domains (especially healthcare, clinical diagnostics, and regulated enterprises) is fundamentally bottlenecked by data silos, privacy laws (HIPAA/GDPR), and distributed compute availability. No single hospital or research lab has enough diverse data or local compute to build robust models alone, yet raw patient data cannot legally or ethically be pooled in a centralized database.

Meanwhile, a massive pool of researchers, clinical data scientists, and compute contributors are willing to participate in distributed model training if provided an intuitive, trustworthy, and auditable platform.

### 1.2 The Vision
A **Kaggle-style collaborative federated learning workbench** where coordinators publish base models and task specifications, and a distributed network of contributors (institutions, researchers, and compute nodes) collaboratively train them:
- **Zero Raw Data Centralization:** Training happens locally on private data partitions (e.g. Hospital A, B, C); only mathematical weight deltas ($\Delta W_k = W_k - W_{\text{global}}$) are transmitted.
- **Kaggle-Grade Experience:** Instead of static leaderboard scoring from CSV predictions, contributors submit **real parameter updates** that get federated and aggregated back into a continuously improving global model.
- **Dual Training Modalities:** Contributors can train directly in-browser using a **low-code, stage-based workspace** (hyperparameter forms + pre-filled PyTorch cells) or train offline via a **lightweight CLI tool** (`fl-platform-cli`) with cryptographic manifest validation.
- **Transparent, Real-Time Job States:** Eliminates all simulated UI and fake animations. Every training run is backed by authentic execution status (`Idle` $\to$ `Queued` $\to$ `Provisioning` $\to$ `Running` $\to$ `Completed` / `Failed`), real backpropagation, epoch loss histories, and live streaming console logs.
- **Data-Dense, Professional Visual Aesthetic:** Replaces consumer-app glassmorphism and decorative gradients with an information-dense, credible, flat design system inspired by Kaggle Competitions, GitHub Actions, and Hugging Face model cards.

---

## 2. Platform Architecture & Separation of Concerns

The platform strictly enforces the architectural boundary between the Central Coordinator and Distributed Client Nodes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CENTRAL COORDINATOR / ADMIN WORKBENCH                    │
│                                                                             │
│  • Model Lifecycle Engine (Draft → Uploaded → Published → Active)           │
│  • Benchmark Dataset Management & Central Evaluation Harness                │
│  • FedAvg Aggregation Orchestrator: W_{t+1} = W_t + \sum (n_k / N) \Delta W_k│
│  • Multi-Factor Adaptive Client Selection (7 scoring dimensions + fairness) │
│  • Mathematical Anomaly Screening: L2 norm bounding & Cosine Filtering      │
│  • Bandwidth Optimization: Top-k Sparsification & 8-bit Quantization        │
│  • LLM Advisory Engine: Structured Pydantic Reasoning & Threat Intelligence │
│  • Real-Time WebSocket Telemetry Stream (/api/v1/ws/telemetry)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                        Global Weights │ Model Updates Only (\Delta W_k)
                        & Checkpoints  │ (Zero Raw Patient Records Transmitted)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 DISTRIBUTED CLINICAL / RESEARCH CLIENT NODES                │
│                                                                             │
│  [Client 1: Hospital A]       [Client 2: Hospital B]       [Client 3: Hospital C]  │
│  • Metropolitan Cohort        • Suburban Cohort            • Community Clinic Cohort│
│  • Private Non-IID CSV        • Private Non-IID CSV        • Private Non-IID CSV    │
│  • PyTorch Local Train        • PyTorch Local Train        • PyTorch Local Train    │
│  • In-Browser / CLI Runner    • In-Browser / CLI Runner    • In-Browser / CLI Runner│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Non-Negotiable Core Rules
1. **Zero Raw Patient Data Leakage (Rule 1 & 6):** Raw records, CSV rows, or patient identifiers never leave the client environment. The central coordinator receives only serialized parameter deltas and audit metadata.
2. **Coordinator Separation (Rule 6):** The Central Coordinator coordinates rounds, verifies deltas, and aggregates global weights, but **never** performs local training.
3. **Model Availability & State Guards (Rules 7, 8, 9, 47):** Clients can only inspect and train on models marked `ACTIVE`. Draft, published, inactive, or archived models are strictly locked (`403 Forbidden` on backend, empty-state on frontend).
4. **Mutual Client Isolation (Rules 15, 16):** Client nodes cannot query or access each other's datasets, metrics, or workspaces.
5. **Deterministic Fallbacks:** All automated LLM advisory systems must operate alongside mathematical fallback logic to prevent non-deterministic execution failures.

---

## 3. Personas & Access Control Matrix

| Persona | Primary Role | Permissions & Workspaces | Key Objectives |
|:---|:---|:---|:---|
| **Platform Admin** | Platform Governance & Infrastructure | Global system controls, user/node management, system health, audit logs | Platform uptime, abuse prevention, node authentication |
| **Coordinator** | Model & Experiment Owner | Model Card creator, experiment orchestrator, round scheduler, pipeline reviewer | Publish tasks, trigger aggregation, evaluate benchmark accuracy |
| **Contributor / Trainer** | Institutional Client or Research Node | Available Models catalog, Cloud Run Workspace, Local CLI runner, update submission | Train on private non-IID shards, tweak hyperparameters, submit deltas |
| **Pipeline Author** | Advanced ML Engineer / Researcher | Custom pipeline proposer, architecture variant author | Submit alternate architectures, loss functions, or optimizers |
| **Compute Donor** | Resource Provider | Compute Node Registry, worker status dashboard | Register spare GPU/CPU, monitor scheduled FL workloads |
| **Observer / Community** | Auditor / Research Community | Public Model Cards, Discussion forums, Leaderboards, Contribution Ledgers | Inspect model cards, participate in discussions, review changelogs |

---

## 4. Current Implementation Baseline (Verified Capabilities)

The platform is backed by a fully tested, production-ready backend and frontend baseline (54/54 Pytest passing):

| Subsystem | Backend Service | API Routes | Verified Functionality |
|:---|:---|:---|:---|
| **Authentication & RBAC** | `auth_service.py` | `/api/v1/auth/*` | JWT Bearer tokens, bcrypt hashing, Admin vs Client role separation, strict client path isolation. |
| **Dataset Governance** | `dataset_service.py` | `/api/v1/admin/datasets/*` | Benchmark clinical ingestion (Diabetes & Heart Disease), CSV upload validation, class balance analyzer. |
| **Model Lifecycle** | `model_service.py` | `/api/v1/admin/models/*`<br>`/api/v1/client/models` | 6-stage state machine (`Draft` $\to$ `Uploaded` $\to$ `Published` $\to$ `Active` $\to$ `Inactive` $\to$ `Archived`). Client endpoint filters strictly for `ACTIVE`. |
| **Private Client Isolation** | `client_data_service.py` | `/api/v1/client/{id}/*` | Non-IID physical partitioning across `data/clients/client_{1,2,3}/`. Directory traversal blocks. Cross-node query rejection (`403 Forbidden`). |
| **Local PyTorch Training** | `trainer_service.py`<br>`ml/models.py` | `/api/v1/client/models/{id}/train` | Genuine PyTorch training (`DiabetesMLP`, `HeartDiseaseMLP`), Adam optimizer, BCE loss, stratified 80/20 train/val split, loss history, delta generation $\Delta W_k$. |
| **Update Submission** | `trainer_service.py` | `/api/v1/client/models/{id}/submit-update` | Delta serialization, L2 norm extraction, sample weighting $n_k$, staging update for coordinator aggregation. |
| **FedAvg Aggregation** | `aggregation_service.py`<br>`fl_coordinator.py` | `/api/v1/admin/experiments/{id}/*` | Weighted parameter aggregation $W_{t+1} = W_t + \sum \frac{n_k}{N}\Delta W_k$, global benchmark evaluation, checkpoint serialization (`exp_{id}/round_{r}_global.pt`). |
| **Live Telemetry** | `telemetry_service.py` | `/api/v1/ws/telemetry`<br>`/api/v1/telemetry/recent` | Real-time WebSocket broadcasting with 50-event circular buffer and client reconnect sync. |
| **Adaptive Client Selection** | `selection_service.py` | `/api/v1/admin/experiments/{id}/client-scores` | 7-factor composite scoring ($w_1 \cdot \text{Perf} + w_2 \cdot \text{Samples} + w_3 \cdot \text{Rel} + w_4 \cdot \text{Qual} - w_5 \cdot \text{Comm} - w_6 \cdot \text{Risk} + \lambda \cdot \text{Fairness}$). |
| **Security & Defense** | `security_service.py` | `/api/v1/admin/security/*` | L2 norm thresholding, cosine similarity outlier filtering, coordinate-wise median aggregation, attack simulation lab. |
| **Bandwidth Optimization** | `compression_service.py` | `/api/v1/admin/compression/*` | Top-k gradient sparsification, 8-bit linear quantization, combined compression saving 75.6% network bandwidth. |
| **LLM Advisory Engine** | `llm_service.py` | `/api/v1/admin/llm/*` | Pydantic schema validation for client selection advisory, threat intelligence, and hyperparameter guidance with deterministic fallback. |

---

## 5. Functional Requirements & Specifications

### 5.1 Model Publishing & Specification Management (Coordinator)
- **Model Registration:** Upload PyTorch architecture definition, target task (`diabetes_prediction`, `heart_disease_risk`, or custom classification/regression), input/output tensor shapes, and initial weight checkpoint.
- **Dataset Specification:** Define schema requirements (feature names, clinical data types, min/max expected ranges, class labels).
- **Default Pipeline Config:** Define standard preprocessing steps, default hyperparameter ranges (`learning_rate`: `0.0001` - `0.1`, `epochs`: `1` - `20`, `batch_size`: `8` - `64`), and aggregation strategy (FedAvg default, Adaptive-FedAvg, Coordinate-Median).
- **Round Scheduling & Eligibility:** Configure round cadence (manual coordinator trigger vs. automated trigger upon receiving $K$ submissions), minimum participant quorum, and security thresholds.
- **State Machine Transitions:**
  - `Draft` $\to$ model created and editable.
  - `Uploaded` $\to$ architecture and initial weights uploaded and verified.
  - `Published` $\to$ visible in catalog as upcoming/review.
  - `Active` $\to$ open for training runs and client round submissions.
  - `Inactive` / `Archived` $\to$ training closed; historical checkpoints preserved.

### 5.2 Low-Code In-Browser Workspace (Cloud Run)
The contributor training workspace shall mirror a structured, modern notebook interface (Kaggle-inspired) designed for clarity and safety:
- **Named Editable Stages:** The training pipeline is broken into clean, labeled execution blocks rather than a monolithic script:
  1. `1. Data Loading & Inspection:` Displays client node identity, private cohort sample count $n_k$, feature distributions, and privacy verification seal.
  2. `2. Preprocessing & Splitting:` Standard scaling (`StandardScaler`), train/val stratified split (80/20).
  3. `3. Model Architecture & Hyperparameters:` Visual form controls (sliders/steppers) for `Epochs`, `Learning Rate`, and `Batch Size`.
  4. `4. Training Execution & Step Optimization:` PyTorch training loop executing on the client's private partition.
  5. `5. Model Delta & Security Metrics:` Computed $\Delta W_k$ payload size (KB), L2 norm $\|\Delta W_k\|_2$, sample contribution weight.
- **Dual-Mode View (Beginner / Advanced):**
  - *Beginner View:* Code is abstracted into visual configuration cards, parameter sliders, and step metrics.
  - *Advanced View:* Reveals the actual underlying PyTorch training code (`torch.optim.Adam`, `torch.nn.BCELoss`, forward/backward pass) in a syntax-highlighted code editor with a "Reset to Recommended Default" action.
- **Pre-Flight Validation:** Automatic checks for parameter boundaries (e.g. learning rate $\in (0, 1]$, epochs $\le 50$) prior to starting the run.
- **Authentic Execution Engine & Real Job States:**
  - `Idle`: Workspace loaded, private data verified, "Start Training" action ready.
  - `Provisioning`: Preparing local tensor memory and data loader.
  - `Running`: Live step-by-step progress, epoch loss tags ($E_1, E_2, \dots, E_n$), real-time loss graph, and an active `Cancel Run` button.
  - `Completed`: Local accuracy, F1 score, delta payload generated. Activates `Transmit to Coordinator` and `Discard` buttons.
  - `Failed`: Error traceback displayed in the logs drawer with a `Retry` action.
- **Persistent Logs Drawer:** Collapsible terminal log viewer displaying timestamped PyTorch execution stdout/stderr (e.g., `[INFO] Epoch 1/3 - Loss: 0.6124 - Val Acc: 78.4%`).

### 5.3 Local Training CLI & Secure Manifest Upload
For institutional nodes and data scientists who train on local on-premise hardware outside the browser:
- **Model Package Export:** One-click download of the `model_bundle.zip` containing:
  - Global weight checkpoint (`global_model.pt`).
  - Pipeline script (`train.py`) and environment lockfile (`requirements.txt`).
  - Standalone runner executable (`fl-platform-cli`).
- **CLI Commands:**
  - `fl-platform-cli info --token <JWT>`: Displays task spec, current active round, and schema rules.
  - `fl-platform-cli train --data-path /path/to/private.csv --epochs 5 --lr 0.01`: Executes PyTorch training locally on on-premise hardware and writes local metrics.
  - `fl-platform-cli submit --output-dir ./run_output`: Generates a signed metadata manifest and transmits only $\Delta W_k$ to the coordinator via `/client/models/{id}/submit-update`.
- **Signed Metadata Manifest:**
  ```json
  {
    "model_id": 1,
    "round_number": 3,
    "base_checkpoint_hash": "sha256:7f83b165...",
    "sample_count": 345,
    "epochs_trained": 5,
    "l2_norm": 0.3841,
    "delta_hash": "sha256:d8e8fca2...",
    "timestamp": "2026-09-04T10:30:00Z"
  }
  ```
- **Web UI Drag-and-Drop Uploader:** An alternate tab in the workspace allowing local practitioners to upload their generated `delta_update.bin` and `manifest.json` directly through the web interface.

### 5.4 Alternate Pipelines & Compute Node Registry
- **Pipeline Proposals:** Contributors can propose alternative training pipelines (e.g., custom learning rate schedulers, alternate optimizer configurations like AdamW or RMSprop, or specialized data augmentation).
- **Coordinator Review Queue:** Proposed pipelines enter a `PENDING_REVIEW` queue. Coordinators can inspect the diff, run an automated sandboxed dry-run, and approve or reject with comments.
- **Compute Node Registry:** Compute donors can register machines (CPU/GPU specs, available memory, availability window, institutional tag) to run background worker processes that pick up queued Cloud Runs.

### 5.5 Multi-Round FedAvg Aggregation & Security Defense
- **Round Lifecycle:**
  1. Coordinator broadcasts global weights $W_t$ to active nodes.
  2. Nodes execute local training on private partitions and submit weight deltas $\Delta W_k^{(t)}$.
  3. **Security Screening:** Each update is evaluated for poisoning attacks:
     - Check L2 norm $\|\Delta W_k\|_2 \le \tau_{\text{norm}}$.
     - Check cosine similarity against the round centroid $\cos(\Delta W_k, \overline{\Delta W}) \ge \tau_{\text{cosine}}$.
     - Flag anomalous updates and trigger defensive aggregation (Coordinate-wise Median or trimmed mean).
  4. **FedAvg Parameter Merging:**
     $$W_{t+1} = W_t + \sum_{k \in S_t} \frac{n_k}{N_t} \Delta W_k^{(t)}$$
  5. **Benchmark Evaluation:** Aggregated model is evaluated against the centralized clinical benchmark dataset (calculating global Accuracy, Loss, F1 score, AUC).
  6. **Checkpoint Persistence:** Serialized to disk and broadcast as the new baseline for round $t+1$.
- **Rollback Capability:** If an aggregated round degrades benchmark metrics, the coordinator can roll back to round $t-1$ with full audit tracking.

### 5.6 Bandwidth Optimization & Compression
- In bandwidth-constrained hospital networks, client nodes can enable **gradient sparsification** and **quantization**:
  - **Top-k Sparsification:** Only the top $k\%$ magnitude parameter deltas are transmitted.
  - **8-Bit Linear Quantization:** Float32 tensors scaled and mapped to Int8.
  - Achieves over 75% bandwidth conservation while maintaining $\ge 98.5\%$ relative convergence accuracy.

### 5.7 LLM Automation & Diagnostic Intelligence
- Integrated AI reasoning using structured Pydantic schemas:
  - **Client Selection Advisor:** Recommends optimal client node participation based on past reliability, data quality, and fairness.
  - **Security Threat Advisor:** Analyzes flagged anomaly vectors and suggests defense countermeasures.
  - **Hyperparameter Convergence Advisor:** Analyzes multi-round loss trajectories and suggests learning rate decaying schedules.
  - **Deterministic Fallback:** If LLM inference is disabled or unreachable, mathematical rule-based algorithms execute seamlessly without system interruption.

### 5.8 Kaggle-Style Model Card Architecture & Collaboration
The Model Card page serves as the central hub for each federated task, organized into clean, Kaggle-style tabs:
1. **Overview:** Executive summary, clinical task objective, target metric, target schema, current global accuracy, active round banner.
2. **Data & Model Spec:** Architecture specifications (layer shapes, activation functions, parameter count), dataset dictionary, feature descriptions, and non-IID client distribution overview.
3. **Pipelines:** Available training pipelines (Default PyTorch baseline + approved community alternate pipelines).
4. **Runs & Submissions:** Tabular ledger of all training runs (Run ID, Client Node / Contributor, Epochs, Local Accuracy, Delta Size, Verification Status, Submitted Timestamp).
5. **Leaderboard:** Contributor rankings based on verified contribution impact score (factoring in sample count, accuracy gain, and participation frequency) rather than raw submission spam.
6. **Discussion:** Threaded discussion threads with Markdown rendering, code snippet formatting, and round feedback.
7. **Changelog & Checkpoints:** Historical progression of global rounds, accuracy improvements, and downloadable global checkpoints.

---

## 6. UI/UX Redesign System (Kaggle-Inspired Workbench Aesthetic)

### 6.1 Design Philosophy: "Data-Dense Workbench"
- **Goodbye to "Flashy AI Demos":** Elimination of dark glowing buttons, glassmorphic blurs, heavy drop shadows, and purple-to-pink gradients.
- **Kaggle / GitHub Clarity:** Crisp borders, high information density, clear tabular layouts, neutral surfaces, and purposeful typography.

### 6.2 Visual Tokens & Color Palette
- **Base Surfaces:**
  - Dark Mode: Surface `#0B0F17` (Deep Slate), Panel `#131B2A`, Border `#1E293B`, Divider `#334155`.
  - Light Mode: Surface `#F8FAFC`, Panel `#FFFFFF`, Border `#E2E8F0`, Divider `#CBD5E1`.
- **Text Hierarchy:**
  - Primary Text: `#F8FAFC` (Dark) / `#0F172A` (Light) - High contrast, legible.
  - Secondary Text: `#94A3B8` (Dark) / `#64748B` (Light) - Subdued, informative.
  - Monospace Font: JetBrains Mono / Fira Code / Consolas for parameters, code snippets, and tensor shapes.
- **Single Accent Family:**
  - Primary Brand Accent: Kaggle Cyan / GitHub Blue (`#0284C7` / `#0EA5E9` / `#38BDF8`), used exclusively for primary action buttons, active tab indicators, and verified links.
- **Flat Semantic Status Badges (No gradients, small pill format):**
  - Success / Merged / Active: Flat Emerald `#059669` / `#10B981` (`bg-emerald-950/40 text-emerald-300 border border-emerald-800/50`).
  - Pending / Queued / In Review: Flat Amber `#D97706` / `#F59E0B` (`bg-amber-950/40 text-amber-300 border border-amber-800/50`).
  - Failed / Rejected / Anomaly: Flat Rose `#E11D48` / `#F43F5E` (`bg-rose-950/40 text-rose-300 border border-rose-800/50`).
  - Idle / Draft / Archived: Flat Slate `#475569` / `#64748B` (`bg-slate-900 text-slate-300 border border-slate-700`).

### 6.3 Component Blueprints
- **Model Card Header Strip:**
  - Model title, task type badge, version tag, license, and active round status.
  - Compact quick-action row: `Start Cloud Run`, `Download Local Bundle`, `Fork Pipeline`.
- **Kaggle-Style Tab Bar:**
  - Flat underline tab bar: `[Overview]  [Data & Model Spec]  [Pipelines]  [Submissions]  [Leaderboard]  [Discussion]  [Changelog]`.
- **Dense Submissions Table:**
  - Uses compact HTML tables (not cards) for high scanability:
    `| Round | Contributor Node | Samples | Local Acc | L2 Norm | Status | Verification | Submitted | Action |`
- **Collapsible Terminal Log Drawer:**
  - Fixed-bottom or card-embedded monospace log container with auto-scroll lock, copy logs action, and step indicators.

---

## 7. Phased Implementation & Rollout Roadmap

```
Phase 1-14: Foundation & Healthcare FL Engine (COMPLETED ✅)
  ├── Fast-API Backend, SQLite, PyTorch MLP Engine, 54/54 Pytest
  ├── Hospital A, B, C Non-IID Partitions & Physical Isolation
  ├── FedAvg Aggregation, WebSocket Telemetry, Security Defense Lab
  ├── Adaptive Client Selection, 8-Bit Quantization, LLM Advisor
  └── Model State Machine & Active Guard

Phase 15: Kaggle-Style UI Overhaul & Job State Engine (TARGET RELEASE)
  ├── Redesign ClientWorkspace.tsx to stage-based notebook layout
  ├── Implement Kaggle-style Model Card Tabs (Overview, Data, Runs, Leaderboard)
  ├── Eliminate glassmorphism; deploy flat, high-density theme
  └── Full Job-State UI (Idle → Provisioning → Running → Completed) with terminal logs

Phase 16: Local Training CLI & Manifest Audit Tool
  ├── Package fl-platform-cli Python CLI tool
  ├── Cryptographic manifest generation and verification
  └── Web drag-and-drop delta file uploader

Phase 17: Community Collaboration & Alternate Pipelines
  ├── Pipeline Author proposal and review workflow
  ├── Contributor Leaderboard and Contribution Ledger
  └── Discussion forum and threaded comments per model

Phase 18: Distributed Compute Registry & Marketplace
  ├── Worker daemon for donor nodes
  └── Central job queue scheduler for multi-backend execution
```

---

## 8. Alignment Gap Analysis & Resolutions

| PRD v1 Draft Element | Current Implementation Reality | Required Change in PRD v2 / Roadmap |
|:---|:---|:---|
| **Simulated "Play" Button** | Backend already has full authentic PyTorch training (`/train`) and FedAvg (`/submit-update`). `ClientWorkspace.tsx` already triggers real PyTorch execution, but visually lacks a notebook-style multi-cell flow and live terminal drawer. | **Resolved:** Clarified in PRD that backend is authentic. PRD focuses on upgrading UI from basic cards to a multi-stage Kaggle notebook workspace with live console logs. |
| **Healthcare Focus vs Generic Open Platform** | Current repository is specifically engineered for Healthcare (Diabetes, Heart Disease, Hospital A/B/C cohorts) with strict clinical privacy constraints. | **Resolved:** PRD establishes a dual-mode strategy: Clinical Consortia / Healthcare is the premier production vertical, while the platform architecture supports generic federated tasks. |
| **Missing Advanced Capabilities in PRD v1** | PRD v1 omitted Adaptive Client Selection, Anomaly Screening (L2/Cosine), Top-k/Quantization Compression, and LLM Automation. | **Resolved:** All 4 existing advanced backend systems are fully integrated into PRD v2 under Sections 4 & 5. |
| **Visual Styling** | Existing frontend used dark glassmorphic panels and glowing borders. PRD v1 demanded Kaggle-style flat data-dense UI. | **Resolved:** Section 6 specifies precise flat visual tokens, eliminating gradients/glassmorphism in favor of a clean, high-density workbench. |
| **Local Training & CLI** | Code currently supports REST API calls for training; no standalone CLI binary exists yet. | **Resolved:** Scheduled as Phase 16 in the roadmap with full schema and CLI specifications defined in Section 5.3. |

---

## 9. Success Metrics & KPIs

1. **System Authenticity:** 100% of training metrics, weight deltas, and round aggregations are computed via real PyTorch tensor operations with zero simulated numbers.
2. **Privacy Assurance:** 0 raw patient records or clinical features ever leave the client node directory or appear in coordinator logs.
3. **Training Velocity:** Time from workspace launch to first local weight delta generation $< 15$ seconds on standard hardware.
4. **Bandwidth Efficiency:** $\ge 70\%$ network payload reduction when compression mode (Top-k + Quantization) is active.
5. **Defensive Robustness:** $100\%$ detection rate of simulated malicious updates (weight poisoning / label flipping) via L2 norm and cosine screening.
6. **User Experience Index:** Zero "is this really training?" support tickets; 100% clarity on job states via real-time step progress and live logs.
