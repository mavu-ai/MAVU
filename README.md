# MAVU: The First Sovereign Emotional AI Guardian 🛡️🇺🇿

![President Tech Award](https://img.shields.io/badge/President_Tech_Award-2025-gold?style=for-the-badge&logo=award)
![Category](https://img.shields.io/badge/Category-Serious_Game-orange?style=for-the-badge)
![AI Models](https://img.shields.io/badge/AI-Psychometric_LLM-blueviolet?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge)

> **"Every child needs a friend. We built one that listens, protects, and stays."**

**MAVU** is a **Next-Gen Emotional AI Game** that serves as a National-Grade Psychological Ecosystem.

We chose the form of a **Game** because play is the universal language of childhood. In a world where children face unprecedented levels of anxiety and loneliness, MAVU uses immersive gameplay as a bridge to build trust, offering a hyper-intelligent **Digital Companion** that provides unconditional emotional support while actively shielding the child from psychological harm.

---

## 💔 The Problem We Solve
**Children are growing up alone.**
*   **The Void**: Ages 5-12 are the most vulnerable. Children are full of fears and questions but often have no one to turn to in the moment of distress.
*   **The Disconnect**: Parents cannot be there 24/7.
*   **The Risk**: 60% of childhood traumas (bullying, grooming, anxiety) go undetected until it is too late.

## 🤝 The MAVU Solution
MAVU is the **Gamification of Emotional Resilience**.
*   **Play to Connect**: Children don't want "therapy"; they want to play. MAVU engages them through interactive storytelling and avatars, creating a safe space where they naturally open up.
*   **Deep Conversation**: Unlike standard games, MAVU uses **Real-time Speech-to-Speech AI** to hold meaningful conversations, helping children navigate complex emotions through play.
*   **A Sentinel**: While the child is having fun with their digital friend, the **neural backend** is ruthlessly analyzing every micro-interaction for safety threats, acting as an invisible guardian.

---

## 🏛️ Ecosystem Architecture

Our Monorepo houses a **High-Performance Distributed Trinity** designed to democratize mental health support for millions of families.

### 1. 🧠 MAVU CORE ( The Sovereign Brain )
*Rank: Enterprise-Grade Backend Hub*
*Tech: Python 3.11, FastAPI Asynchronous, OpenAI Realtime, Vector & Graph DBs*

The cognitive center. MAVU CORE is engineered to handle the complexity of human emotion.
*   **🛡️ "THE GUARD" (Tier-4 Safety Engine)**: A separate neural layer that monitors conversation in real-time.
    *   *Detects*: Bullying, Grooming, Depression, Self-Harm.
    *   *Acts*: Softly calms the child while simultaneously alerting the parent with meta-data (not invasions of privacy).
*   **🧬 Psycho-Emotional RAG**: We don't just remember facts; we remember *feelings*. MAVU remembers that the child was sad about a lost toy three days ago and checks in on them, building deep trust.
*   **🗣️ Child-Adapted LLM**: Custom fine-tuned models that speak with the vocabulary, tone, and patience required for a 6-year-old, stripping away the robotic coldness of standard AI.

### 2. 🎮 MAVU CLIENT ( The Immersive Interface )
*Rank: Immersive Interaction Layer*
*Tech: Unity 6 (LTS), Live2D Cubism 5.0, Native C# Networking*

A console-quality mobile experience that brings the "Soul" to the machine.
*   **🗣️ Full-Duplex Voice Engine**: Natural interruption, laughter, and whispers. No "Push-to-Talk". Just a real conversation with a friend who is always there.
*   **🎭 Procedural Empathy**: The avatar's face isn't just animated; it *reacts*. If the child sounds sad, MAVU looks concerned. If the child laughs, MAVU smiles. This is **Audio-Driven Micro-Expression Technology**.
*   **📱 Native Kernel Optimization**: Crystal clear voice isolation even in noisy environments using custom `iOSAudioFix` bridges.

### 3. 🌐 PARENTAL INSIGHT ( The Oversight )
*Rank: Analytics & Control Center*
*Tech: React 19, Vite, TailwindCSS, Recharts*

For parents, MAVU is a tool of **Understanding, not Control**.
*   **📊 Emotional Weather Map**: Instead of spying on chats, parents see an "Emotional Dashboard". ("Your child felt anxious today about 'School' around 2:00 PM").
*   **🚨 Threat Radar**: Instant push notifications if critical safety thresholds are breached.
*   **💳 Frictionless National Payment**: Built-in support for Uzcard/Humo/Payme for mass accessibility in Uzbekistan.

---

## 🚀 Why MAVU Wins the President Tech Award

| Feature | The Old World (Apps) | The MAVU Era (Ecosystem) |
| :--- | :--- | :--- |
| **Engagement** | Boring Lessons | **Immersive Gamification** |
| **Role** | Tool / Toy | **Friend & Guardian** |
| **Technology** | Chatbot / Text | **Real-time Multimodal Empathy Engine** |
| **Privacy** | Surveillance | **Insight & Protection (Zero-Trust Privacy)** |
| **Target** | Academic Grades | **Psychological Resilience** |

---

## 🛠️ The Artillery (Tech Stack)

**Artificial Intelligence Layer**
*   **LLM Orchestration**: OpenAI Realtime API (GPT-4o derived) + Custom Child-Psychology Fine-tuning
*   **Safety Layer**: Proprietary Guard-Models for real-time toxicity filtering
*   **Memory**: Weaviate (Vector) for long-term emotional context

**Client-Side Engineering**
*   **Engine**: Unity 6 (6000.0.43f1) - Utilizing Data-Oriented Technology Stack (DOTS)
*   **Animation**: Live2D Cubism SDK - Procedural LipSync & Expression
*   **Audio**: Native `System.Net.WebSockets` for raw PCM streaming

**DevOps & Infrastructure**
*   **Containerization**: Docker & Docker Compose (Microservices pattern)
*   **Security**: End-to-end encryption (TLS 1.3) and GDPR/COPPA compliance

---

## 🏎️ Deployment Strategy & Operations Protocol

Follow this protocol to deploy the full Sovereign Infrastructure.

### Prerequisites
*   **Docker Desktop** (latest version)
*   **Node.js** v20+
*   **Python** 3.11+
*   **Unity Hub** (Unity 6 / 6000.0.x)

### Phase 1: Ignite the Core (Backend)
1.  **Navigate to the Neural Center**:
    ```bash
    cd mavu-core/mavu_fullstack-main/backend
    ```
2.  **Configure Environment Variables**:
    ```bash
    cp .env.example .env
    ```
    > **CRITICAL**: Populate `OPENAI_API_KEY` in `.env`.
3.  **Launch Infrastructure Containers**:
    ```bash
    cd ..
    docker-compose up -d
    ```
4.  **Activate the Neural Interface (API)**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

### Phase 2: Launch Mission Control (Web Dashboard)
1.  **Initialize the Portal**:
    ```bash
    cd ../../../mavu-landing
    npm install
    npm run dev
    ```

### Phase 3: Connect the Client (Unity Mobile App)
1.  Open **Unity Hub**.
2.  Open Project: `mavu-game/MavuAI-main`.
3.  In `Assets/Scenes/Main.unity`, verify `MavuRealtimeService` is pointing to `ws://localhost:8000/ws`.
4.  **Press Play**. MAVU is now listening.

---

## 🔮 The Roadmap (2025-2026)

*   **Q4 2025**: **Open Beta & Investment Rounds**.
*   **Q1 2026**: **Global Partnerships & Accelerators**.
*   **Q2 2026**: **Launch of Proprietary Model**. Drastically reducing inference costs by 50% ($3-4 margin per user).
*   **Q4 2026**: **100,000+ Active Subscribers**. Mass adoption.

---

<div align="center">

**🇺🇿 PROUDLY DEVELOPED FOR THE PRESIDENT TECH AWARD 2025 🇺🇿**

*"We are creating a friend. And that changes everything."*

</div>
