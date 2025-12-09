# Mavu: Your AI Companion for Learning

**Mavu** is a next-generation interactive AI assistant designed to spark curiosity and engage children through conversational learning. By combining real-time voice intelligence with expressive **Live2D** avatars, Mavu transforms education into a lively, emotional, and immersive dialogue.

-----

## 🌟 Key Features

### 🗣 Seamless Real-Time Speech-to-Speech

Forget "press-to-talk." Mavu offers a true conversational experience with ultra-low latency.

  * **Intelligent VAD (Voice Activity Detection):** The system smartly distinguishes between speech and silence, ensuring Mavu listens attentively and interrupts only when appropriate.
  * **Smart Audio Resampling:** Built-in DSP algorithms automatically bridge the gap between device hardware (48kHz) and AI model requirements (24kHz), eliminating pitch artifacts.

### 🎭 Immersive Live2D Avatars

Interaction goes beyond just audio. Mavu brings characters to life with emotional responsiveness.

  * **Procedural LipSync:** Mouth movements are driven dynamically by the audio amplitude stream for near-perfect synchronization.
  * **Runtime Customization:** Hot-swap skins, outfits, and character models instantly without restarting the session.
  * **Reactive Animations:** Characters respond visually to the context of the conversation.

### 📱 Cross-Platform Architecture

Built with a "write once, deploy everywhere" mindset, optimized for both major mobile ecosystems.

  * **iOS:** Native `AVAudioSession` handling for robust "PlayAndRecord" support (works even in silent mode).
  * **Android:** Optimized microphone buffer handling and permission management for diverse hardware support.
  * **Deep Linking:** Integrated deep link support for seamless authentication and email verification flows.

-----

## 🛠 Technical Stack

  * **Engine:** Unity 6 (6000.0.43f1)+
  * **Core Logic:** C\# (Async/Await pattern, Native WebSockets)
  * **Visuals:** Live2D Cubism SDK for Unity
  * **Networking:** Custom JSON-based binary protocol over `System.Net.WebSockets`
  * **Platforms:** iOS & Android

-----

## 🧩 Architecture Overview

### Core Services

  * **`MavuRealtimeService`**: The neural center of the app. It orchestrates the WebSocket lifecycle, captures raw microphone PCM data, performs real-time resampling, and streams audio directly to Unity's main thread.
  * **`AuthService`**: Manages secure user authentication, session tokens, and profile synchronization.
  * **`AppManager`**: A state-machine based UI orchestrator handling transitions between Login, Gameplay, and Onboarding flows.

### Visual Integration

  * **`MavuLive2DLipSync`**: A bridge component that translates volume data from the realtime service into `ParamMouthOpenY` Live2D parameters.
  * **`ModelsHandler`**: Handles asynchronous loading of Addressables/Resources for character customization.

### Protocol Details

Communication with the MavuAI backend uses a high-efficiency custom protocol:

  * **Audio Output:** `audio.append` (Base64 encoded PCM16)
  * **Audio Input:** `audio.delta` (Base64 encoded PCM16)
  * **Transcript:** `transcription` (Real-time text feedback)

-----

## 📦 Installation & Setup

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/aliexprojects/mavu-unity-client.git
    ```

2.  **Open in Unity:**

      * **Recommended version:** Unity 6 (6000.0.43f1) or newer.

3.  **Check Dependencies:**

      * Ensure the **Live2D Cubism SDK** is correctly imported in `Assets/`.
      * **iOS Specific:** Check `Plugins/iOS/` for `iOSAudioFix.mm`.

4.  **Configuration:**

      * Select the `MavuRealtimeService` context in your scene.
      * Verify the **Socket URL** points to the correct environment (e.g., `wss://mavu-api.aey-inc.uz/api/v1/realtime`).

-----

## 📱 Build Notes

### 🍎 iOS

The project includes a native plugin (`iOSAudioFix.mm`) to manage `AVAudioSession`.

  * **Privacy:** Ensure `NSMicrophoneUsageDescription` is set in **Project Settings \> Player \> iOS**.
  * **Behavior:** The app enforces `PlayAndRecord` with `DefaultToSpeaker` to override the hardware silent switch.

### 🤖 Android

Ensure your Android Manifest includes the necessary permissions for real-time audio capture.

  * **Permissions:**
      * `android.permission.RECORD_AUDIO`
      * `android.permission.INTERNET`
  * **Configuration:** Set **Internet Access** to "Require" in Player Settings to ensure WebSocket stability.

-----

## 📄 License & Credits

**Copyright © 2025 aliexprojects / MavuAI. All rights reserved.**

Developed for educational and entertainment purposes. This client serves as the frontend for the MavuAI platform.

-----
