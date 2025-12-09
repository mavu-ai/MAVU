# Mavu: Your AI Companion for Learning

**Mavu** is an interactive AI-powered assistant designed to spark curiosity and engage children in conversational learning. Through real-time voice interaction and expressive Live2D avatars, Mavu makes discovering new facts and exploring the world engaging and fun.


---

## 🌟 Key Features

### 🗣️ Real-Time Speech-to-Speech
Experience seamless, low-latency conversations. Mavu listens, understands, and responds instantly, creating a natural dialogue flow powered by advanced AI models.
* **Voice Activity Detection (VAD):** Smart microphone handling ensures Mavu listens when you speak and waits politely when it's responding.
* **Adaptive Resampling:** Automatic audio conversion between device rates (48kHz) and server requirements (24kHz) prevents audio artifacts like pitch shifting.

### 🎭 Expressive Live2D Avatars
Interaction goes beyond voice. Mavu features fully animated Live2D characters that react emotionally to the conversation.
* **Procedural LipSync:** Mouth movements are driven directly by the audio stream amplitude for perfect synchronization.
* **Dynamic Skins:** Support for hot-swapping character models and skins at runtime without interrupting the session.
* **Customization:** Change outfits, colors, and accessories to personalize the experience.

### 📱 Mobile-First Design
Optimized for mobile platforms with platform-specific enhancements.
* **iOS Audio Session Management:** Automatic handling of audio categories to support "PlayAndRecord" modes, ensuring loud and clear output through the speaker even in silent mode.
* **Deep Linking:** Support for login and email verification via deep links.

---

## 🛠 Technical Stack

* **Engine:** Unity 6 (6000.0.43f1)+
* **Language:** C# (Async/Await, Native WebSocket)
* **Visuals:** Live2D Cubism SDK for Unity
* **Networking:** Custom JSON-based WebSocket protocol over `System.Net.WebSockets`
* **Platforms:** iOS (Primary), Android (Planned)

## 🧩 Architecture Overview

### Core Services
* **`MavuRealtimeService`**: The heart of the application. Manages the WebSocket connection, microphone capture, audio resampling, and stream decoding. It pushes raw PCM audio data directly to Unity's audio thread.
* **`AuthService`**: Handles user authentication via promo codes, session token management, and profile updates.
* **`AppManager`**: Central UI orchestrator managing application states (Login, Main App, Registration).

### Visual Integration
* **`MavuLive2DLipSync`**: A bridge component that reads volume data from the realtime service and drives the `ParamMouthOpenY` Live2D parameter. Supports dynamic model binding.
* **`ModelsHandler`**: Manages character instantiation, customization, and switching.

### Protocol Details
The app communicates with the MavuAI backend via a custom WebSocket protocol:
* **Audio Output:** `audio.append` (Base64 PCM16)
* **Audio Input:** `audio.delta` (Base64 PCM16)
* **Transcript:** `transcription` (Text)

---

## 📦 Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/aliexprojects/mavu-unity-client.git](https://github.com/aliexprojects/mavu-unity-client.git)
    ```
2.  **Open in Unity:**
    * Use Unity Hub to open the project (Version 6000.0.43f1 or newer recommended).
3.  **Dependencies:**
    * Ensure the Live2D Cubism SDK is properly imported in `Assets/`.
    * Check `Plugins/iOS/` for `iOSAudioFix.mm` (Required for iOS builds).
4.  **Configuration:**
    * Locate the `MavuRealtimeService` component in the scene.
    * Verify the **Socket URL** matches your backend environment (e.g., `wss://mavu-api.aey-inc.uz/api/v1/realtime`).

---

## 📱 iOS Build Notes

For iOS builds, the project includes a native plugin (`iOSAudioFix.mm`) to manage `AVAudioSession`.
* **Microphone Usage Description:** Ensure `NSMicrophoneUsageDescription` is set in Project Settings > Player > iOS.
* The app automatically switches the audio session to `PlayAndRecord` with `DefaultToSpeaker` options to override silent mode during conversations.

---

## 📄 License & Credits

**Copyright © 2025 aliexprojects / MavuAI.** All rights reserved.

Developed for educational and entertainment purposes. This client serves as the frontend for the MavuAI platform.