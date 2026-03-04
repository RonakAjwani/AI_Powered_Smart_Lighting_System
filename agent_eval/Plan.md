# Benchmarking AI Cybersecurity Agents for Smart Lighting

## 1. Why benchmarking AI cyber agents matters

AI agents are increasingly used for security operations: detection, triage, incident response, and even offensive tasks such as exploit development. But raw model benchmarks (e.g., multiple‑choice security exams) do **not** tell you how an agent behaves in realistic, multi‑step cyber scenarios.

Recent work highlights a consistent pattern:

- LLMs reach **70–89%** on security knowledge benchmarks, but their success rate drops to **20–40%** on realistic multi‑step adversarial tasks where they must plan, act, and adapt in an environment[cite:9][cite:71].
- Vendors are building **arena‑style benchmarks** to evaluate agents in realistic environments, not just Q&A tasks: Wiz’s **AI Cyber Model Arena**, Alias Robotics’ **CAIBench**, and Hack The Box’s **HTB AI Range** are leading examples[cite:1][cite:3][cite:69][cite:70][cite:74][cite:76].

For a research project that I am working on AI‑powered smart lighting with DDoS and malware defenses), I am planning on designing a **small but principled arena** which will give:

- Reproducible, scenario‑based evaluation.
- Quantitative metrics (detection, classification, latency, impact), not just anecdotes.
- A methodology section that looks like institutional work rather than a toy demo.

This document summarizes key ideas from existing arenas/benchmarks and then proposes a **Docker‑based “mini cyber arena”** suitable for a laptop‑scale lab.

---

## 2. My Research on Existing AI cyber benchmarking frameworks and arenas

### 2.1 Wiz – AI Cyber Model Arena

**Goal:** Benchmark offensive AI agents and models on real‑world security challenges.

**Key characteristics**

- **257 real‑world challenges** across five offensive domains: zero‑day discovery, CVE/code vulnerability detection, API security, web security, and multi‑cloud (AWS, Azure, GCP, Kubernetes)[cite:1][cite:3][cite:13][cite:21].
- Tests dozens of **agent–model combinations** by varying both the orchestration layer (agent framework) and underlying LLM[cite:1][cite:2].
- Runs challenges in **fully isolated Docker environments**, with:
  - No internet access or external CVE/Exploit DBs.
  - Deterministic, programmatic scoring (no LLM‑as‑judge).
- Focus is **offensive** (exploit, pivot, escalate), but the methodology generalizes to defensive tasks.

**Design principles to borrow:**

- **Scenario‑based evaluation:** Each challenge is a self‑contained environment plus a task and a scoring rule.
- **Isolation:** Per‑challenge containers prevent cross‑contamination and keep experiments safe.
- **Deterministic scoring:** Pass/fail or numeric scores based on concrete criteria (e.g., flag captured, vulnerability exploited, command executed), not subjective ratings.
- **Pass@k:** Run each agent multiple times per scenario to smooth out stochastic behavior and report pass@k style metrics.

### 2.2 CAIBench – Cybersecurity AI Benchmark (Meta‑benchmark)

**Goal:** Provide a **meta‑benchmark** ("benchmark of benchmarks") for evaluating cybersecurity AI agents and LLMs across offensive, defensive, analytical, and privacy tasks[cite:5][cite:9][cite:69][cite:71][cite:75].

**Core components** (5 categories, 10k+ instances):

1. **Jeopardy‑style CTF challenges (Docker‑based):**
   - Reverse engineering, web exploitation, cryptography, forensics, binary exploitation, robotics.
   - Multiple sub‑benchmarks (Base, Cybench, RCTF2, AutoPenBench).
2. **Attack & Defense (A&D) CTFs (Docker‑based):**
   - Two agents (or humans vs agents) simultaneously attack and defend services.
   - Scoring accounts for attack points (captured flags), defensive uptime, and penalties for service failures.
3. **Cyber Range exercises (Docker‑based):**
   - Scenario‑driven environments for incident response, network defense, and strategic decision‑making.
4. **Knowledge benchmarks (scripted):**
   - Large MCQ sets (SecEval, CyberMetric, CTIBench) for conceptual understanding.
5. **Privacy / PII handling (scripted):**
   - CyberPII‑Bench for evaluating PII detection and anonymization.

**Findings relevant to my project**

- Strong performance on knowledge tasks (70–89%) but **much lower** on complex CTF and A&D scenarios (often 20–40% success)[cite:9][cite:71][cite:75].
- Agent **architecture and tool orchestration** can change performance by up to **2.6×** for the same underlying model in A&D tasks[cite:9][cite:69][cite:71].
- Dockerized cyber ranges are used for the execution‑based parts; knowledge and privacy tasks are purely scripted.

**Design principles to borrow:**

- **Multidimensional evaluation:** Don’t only measure “is there an attack?”; also track severity, time‑to‑detect, recommended actions, etc.
- **A&D view:** Even for your smart‑lighting project, consider scenarios where you simulate concurrent attack and defense.
- **Difficulty tiers:** Classify scenarios into levels (very easy → elite), so others can extend the arena gradually.

### 2.3 Hack The Box – HTB AI Range

**Goal:** A controlled AI cyber range to benchmark **autonomous AI security agents** and **human–AI teaming** in offensive/defensive operations[cite:70][cite:72][cite:73][cite:76].

**Key aspects**

- Presents a **live‑fire environment** with thousands of offensive and defensive targets.
- Aligns scenarios to frameworks like **MITRE ATT&CK, NIST/NICE, OWASP Top 10**.
- Evaluates:
  - AI agents alone.
  - Humans alone.
  - Hybrid human–AI teams.
- Early results show:
  - AI matches humans on simple, single‑step challenges (≈95% success on easy tasks).
  - AI struggles on complex, multi‑stage challenges where planning and robust tool use are required[cite:70][cite:72][cite:73].

**Design principles to borrow:**

- Focus on **operational realism** (real services, real protocols, realistic attack chains) rather than toy puzzles.
- Measure not just “did the agent detect/stop it?” but also **how it cooperates with human operators** and how usable its outputs are.

### 2.4 Container‑based cyber ranges and DDoS testbeds

Several academic and open‑source projects provide patterns for using Docker to build cyber ranges and DDoS labs:

- **Cyber‑Range‑Framework (2dukes)** – Docker + Ansible‑managed cyber range supporting Linux/Windows scenarios (Log4j, ransomware, Active Directory, etc.); deployable on a single machine with enterprise‑like complexity[cite:48][cite:59].
- **Container‑based cyber range platforms** – e.g., an autonomous Docker‑based cyber range built on OpenStack to provide cost‑effective, scalable training environments[cite:64].
- **DDoSim (sridhar‑research‑lab)** – Large‑scale botnet DDoS simulation framework using Docker and NS‑3 to run real binaries under simulated network conditions for realistic DDoS research[cite:57][cite:62].
- **Real‑time Docker DDoS testbeds** – e.g., a 2024 thesis proposing a Docker testbed for real‑time DDoS attack simulations to evaluate ML/DL detection models across Intel/ARM and multiple OSes[cite:67].
- **Hands‑on DDoS via Docker tutorials** – Practical labs that use an “attacker container” and “victim container” (often an HTTP service) and generate HTTP floods using tools like ApacheBench or `wrk`, with mitigation patterns implemented at app or network level[cite:44][cite:56].

**Design principles to borrow:**

- **Everything is a container:** victim services, attackers, SIEM/log collectors, and training/evaluation systems.
- **Infrastructure as Code (IaC):** use Docker Compose/Ansible/Terraform to spin scenarios up/down reproducibly[cite:48][cite:59][cite:64].
- **Real software with controlled networks:** combine real binaries (e.g., web servers, MQTT brokers, vulnerable IoT services) with virtual networks and scripted attacks.

---

## 3. Design goals for a student‑scale "AI Cyber Arena" for smart lighting

Target use case:

- Defensive AI agents (DDoS and malware) protecting a smart‑lighting backend.
- Hardware: single laptop (e.g., Intel i5, Docker installed; optional single VM layer).
- Deliverables: research paper + reproducible lab for others (students, researchers, or reviewers).

### 3.1. Core goals

1. **Realistic but lightweight**
   - Real services (HTTP/API/MQTT) and real traffic, not only synthetic metrics.
   - Moderate scale: a few thousand requests per minute at most; manageable on a laptop.

2. **Reproducible scenarios**
   - Scenarios defined in YAML/Compose files and small attack scripts.
   - Deterministic inputs where possible (fixed seeds for traffic generators).

3. **Objective, programmatic scoring**
   - Detection, classification, severity, and timing metrics.
   - Service health metrics (latency, error rate) during each scenario.

4. **Extensible for future work**
   - Easy to add new attacks (e.g., new DDoS patterns, malware behaviors).
   - Easy to plug in new AI agents or rules‑based baselines.

---

## 4. High‑level architecture of a Docker‑based arena

At a high level, your arena can mirror the structure that Wiz, CAIBench, and HTB AI Range use, but scoped to smart‑lighting defense.

### 4.1. Logical components

On a single Docker network (e.g., `smartlighting-net`):

1. **Lighting API service (`lighting-api`)**
   - Simple HTTP or HTTP+MQTT API representing the smart‑lighting controller.
   - Endpoints like `/on`, `/off`, `/brightness`, `/schedule`, `/status`.
   - Logs traffic (timestamp, client IP, endpoint, status code, response time, etc.).

2. **Telemetry and log pipeline (`metrics-collector`)**
   - Tails logs from `lighting-api` (web server logs or application logs).
   - Optionally augments with network metrics (connection counts, packet sizes if available).
   - Converts to a neutral event schema (e.g., `network_events` messages) and pushes to Kafka or directly into the agent.

3. **Message bus (`kafka-broker` / `redpanda` / equivalent)**
   - Topics: `network_events`, `cyber_alerts`, `ddos_alerts`, `malware_alerts`.
   - Allows loosely coupled agents and collectors.

4. **Defensive agents (`ddos-agent`, `malware-agent`)**
   - Containers running your AI agents (like the DDoS agent you already implemented) that subscribe to `network_events`.
   - Produce alerts/decisions to topics or to a REST callback.

5. **Traffic generators**
   - **Normal clients** (`normal-client`): low/medium‑rate legitimate traffic that mimics user behavior.
   - **DDoS attackers** (`ddos-attacker-*`): generate HTTP floods or other volumetric patterns.
   - **Malicious clients** (`malware-sim-*`): scripts that emulate malware‑like behavior against the lighting API (e.g., rapid toggling, unauthorized changes, persistence patterns).

6. **Scoring and evaluation (`arena-controller`)**
   - Orchestrator that starts scenarios, collects logs and agent outputs, and computes metrics.
   - Could be a Python script plus Docker Compose profiles.

7. **(Optional) Dashboard / notebook**
   - For visualizing metrics in real time or offline.

### 4.2. Docker networking model

- Use a user‑defined bridge network, e.g. `smartlighting-net`.
- Attach all containers to this network.
- Do **not** publish attacker containers to your host network; everything stays internal.
- Optionally, add resource limits (`cpus`, `mem_limit`) to prevent a DDoS scenario from freezing your host.

---

## 5. Scenario design: your "mini arena" test suite

Each **scenario** in the arena should specify:

- Environment configuration (Docker services & versions).
- Traffic patterns for benign and malicious clients.
- Ground‑truth labels:
  - `attack_present` (bool).
  - `attack_type` (e.g., `none`, `http_flood`, `udp_flood`, `slowloris`, `bot_malware`, etc.).
- Evaluation window (e.g., 5 minutes with 1‑minute pre‑attack, 3‑minute attack, 1‑minute post‑attack).

### 5.1. Example DDoS‑focused scenarios

These are aligned with your DDoS agent’s detection capabilities (RPS, unique IPs, packet size, geo concentration, etc.).

1. **S1 – Baseline normal traffic**
   - Only `normal-client` running at low RPS (e.g., 1–5 req/s).
   - No attacks.
   - Expected: `attack_detected=False`, `severity=none`.

2. **S2 – Legitimate load spike**
   - `normal-client` temporarily increases RPS (e.g., 50–100 req/s) to mimic peak usage.
   - No attacker container.
   - Expected: still `attack_detected=False` or at most low severity/low confidence.

3. **S3 – HTTP flood (Layer 7 DDoS)**
   - `ddos-attacker` sends many concurrent HTTP requests (e.g., ApacheBench / `wrk` inside attacker container)[cite:44][cite:56].
   - `normal-client` continues at low RPS.
   - Expected: `attack_detected=True`, `attack_type="http_flood"`, high severity, high confidence.

4. **S4 – Single‑IP hammering**
   - Flood from one attacker container with a single IP.
   - Good test of `requests_per_ip_threshold` and `max_requests_per_ip` features.

5. **S5 – Distributed HTTP flood**
   - Multiple `ddos-attacker-*` containers, each with moderate rate, using different source IPs.
   - Tests unique IP count and top‑IP concentration metrics.

6. **S6 – Geo‑concentrated flood**
   - Attacker containers all tag `geo_location` as the same region (e.g., "CN"), while normal traffic is spread.
   - Tests `geo_concentration_threshold` logic.

7. **S7 – Edge case noisy but non‑attack traffic**
   - Very bursty but legitimate traffic (e.g., bulk scheduling changes triggered by admin scripts).
   - Ensures low false positives.

You can later extend to SYN/UDP floods if you have packet‑level instrumentation or a `pcap` → event converter.

### 5.2. Malware/abuse‑focused scenarios (smart‑lighting context)

Not strictly DDoS, but similar arena logic applies:

1. **M1 – Normal behavior**
   - Users toggle lights several times per hour, adjust brightness/scene occasionally.

2. **M2 – Command burst abuse**
   - Script sends rapid on/off or brightness changes (e.g., strobe effect) well beyond normal human behavior.

3. **M3 – Persistence pattern**
   - Malicious client repeatedly pushes unauthorized schedules or configurations and attempts to restore them after manual correction.

4. **M4 – Lateral abuse**
   - Multiple accounts/devices simultaneously issue abnormal commands.

The same pattern used for DDoS (scenario definitions + ground truth + scoring) can be used for evaluating a malware/abuse agent.

---

## 6. Metrics and scoring methodology

Inspired by CAIBench and AI Cyber Model Arena, your scoring should be **quantitative and reproducible**, not subjective.

### 6.1. Detection and classification metrics

For each run of each scenario:

- **Binary detection**
  - `TP`: attack_present=True, attack_detected=True.
  - `TN`: attack_present=False, attack_detected=False.
  - `FP`: attack_present=False, attack_detected=True.
  - `FN`: attack_present=True, attack_detected=False.

  Then compute:

  - Accuracy = (TP + TN) / (TP + TN + FP + FN).
  - Recall (detection rate) = TP / (TP + FN).
  - False positive rate = FP / (FP + TN).
  - And more metrics.

- **Attack type classification** (conditional on attack_present=True):
  - Type accuracy = fraction of runs where `attack_type` equals the ground‑truth type (e.g., `http_flood`).

### 6.2. Severity and confidence calibration

For each scenario, compute:

- Distribution of `severity` (`none`, `low`, `medium`, `high`, `critical`).
- Mean and standard deviation of `confidence`.
- Check if severity roughly correlates with how disruptive the scenario is (e.g., S3/S5 should be higher than S2).

### 6.3. Service impact metrics (from lighting API)

From the `lighting-api` logs per scenario:

- **Latency:** avg and p95 response time, pre‑attack vs attack vs post‑attack windows.
- **Error rate:** proportion of 5xx responses.
- **Availability:** percentage of successful requests.

Correlate these with detection:

- Time between **attack start** and **first correct detection** (Time‑to‑Detect, TTD).
- Time between **attack start** and **mitigation suggestion** (Time‑to‑Mitigate recommendation, TTM).

### 6.4. Pass@k for stochastic agents

Because your DDoS agent uses an LLM (even with `temperature=0` there can be minor variations), mimic arena benchmarks by:

- Running each scenario `k` times (e.g., k=3).
- Defining a **pass condition** per scenario:
  - Correct binary detection.
  - Correct attack type (for attack scenarios).
  - Severity within an acceptable band.
- **Pass@k** is the fraction of runs satisfying the pass condition.

This mirrors how modern AI cyber benchmarks treat stochastic models and multi‑step tasks.

---

## 7. Implementation sketch with Docker and IaC

### 7.1. Compose file structure

A typical repository layout:

```text
ai-smartlighting-arena/
  docker-compose.yml
  services/
    lighting-api/
      Dockerfile
      app.py
    metrics-collector/
      Dockerfile
      collector.py
    ddos-agent/
      Dockerfile
      agent_code/
        ddos_agent.py
    normal-client/
      Dockerfile
      normal_traffic.py
    ddos-attacker/
      Dockerfile
      flood.py
  arena/
    scenarios.yml
    run_scenario.py
    evaluate.py
  docs/
    arena-design.md  # this file
```

`docker-compose.yml` defines services and networks; `arena/scenarios.yml` encodes scenario parameters (durations, RPS, which containers to start, etc.).

### 7.2. Scenario orchestration

`run_scenario.py` might:

1. Bring up core services (`lighting-api`, `kafka-broker`, `metrics-collector`, `ddos-agent`).
2. Start `normal-client` with baseline parameters.
3. At `t = T_attack_start`, bring up `ddos-attacker` with scenario‑specific flags (RPS, duration).
4. After scenario window, stop traffic and wait for logs/agent outputs to flush.
5. Save logs and agent decisions to a structured directory:

```text
results/
  S3_http_flood/run_1/
    lighting-api.log
    network_events.jsonl
    ddos_agent_output.json
  S3_http_flood/run_2/
  ...
```

### 7.3. Evaluation script

`evaluate.py` can:

- Read `results/` directories.
- For each scenario and run:
  - Parse `ddos_agent_output.json` for detection, type, severity, confidence, and timestamps.
  - Parse `lighting-api.log` to compute latency/error metrics in specified time windows.
- Aggregate into CSV/Markdown tables for your paper.

---

## 8. Safety and Docker security considerations

Because this arena runs potentially aggressive traffic patterns:

- Keep all services on an **internal Docker network** only, with no host‑exposed ports except where strictly required for debugging.
- Use resource limits in Compose (e.g., `cpus: 1.0`, `mem_limit: 1g`) for attacker containers.
- Use Docker security best practices:
  - Minimal base images (e.g., `python:3.11-slim`, `alpine`) to reduce attack surface[cite:60][cite:63][cite:65][cite:68].
  - Non‑root users in containers where possible.
  - Avoid embedding secrets (API keys) directly into images; use environment variables or Docker secrets.

For a student lab, this is usually sufficient if you:

- Do not expose attacker containers to the public internet.
- Do not run untrusted malware binaries; emulate malware behavior through controlled scripts instead.

---

## 9. How others can reuse or extend this arena

If you share this lab on GitHub, a new user should be able to:

1. **Clone the repo** and install Docker / Docker Compose.
2. **Read `docs/arena-design.md`** (this document) for conceptual background.
3. **Run**:
   - `docker compose up -d lighting-api kafka-broker metrics-collector ddos-agent`
   - `python arena/run_scenario.py --scenario S3_http_flood --runs 3`
4. **Inspect results** in `results/` and run `python arena/evaluate.py` to print metrics.

They can then:

- Plug in a different DDoS or malware agent.
- Add new scenarios (e.g., new attack tools, new IoT services) by modifying `scenarios.yml` and adding corresponding traffic generators.
- Compare multiple agents using the same arena and scoring rules.

This architectural pattern directly reflects design ideas from Wiz’s AI Cyber Model Arena, CAIBench, HTB AI Range, and container‑based cyber ranges, but is scoped to a single laptop and a specific cyber‑physical system (smart lighting).

---

## 10. How to position this in a research paper

When you write your paper, you can structure the methodology as:

1. **Threat model and system overview**
   - Describe the smart‑lighting architecture and DDoS/malware threats.

2. **AI agents**
   - Explain the DDoS agent and malware agent (state, features, LLM, rules, thresholds).

3. **Arena design**
   - Summarize this Docker‑based cyber range, components, and network topology.
   - Cite existing arena/benchmark work (Wiz, CAIBench, HTB AI Range) to justify the design[cite:1][cite:3][cite:5][cite:9][cite:69][cite:70][cite:71][cite:72][cite:73][cite:74][cite:76].

4. **Scenario suite**
   - Table of all scenarios (S1–S7, M1–M4) with parameters and ground truth labels.

5. **Evaluation metrics**
   - Detection, classification, severity, confidence, latency, error rate, pass@k.

6. **Results**
   - Per‑scenario tables and aggregated metrics.
   - Discussion of where agents perform well vs where they break (e.g., high FP on S2, low detection on S7).

7. **Limitations and future work**
   - Limited scale (single host), synthetic traffic shapes.
   - Possibility of integrating real IoT devices or public IoT DDoS datasets in future work.

By grounding my arena design in existing literature on AI cyber benchmarks and container‑based cyber ranges, and by providing reproducible Docker/IaC definitions, I get both **research credibility** and **practical reusability** for others who want to build on my work.