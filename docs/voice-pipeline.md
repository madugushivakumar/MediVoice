# MediVoice — Pipecat Voice Pipeline Documentation

## 1. Pipeline Overview
The real-time voice pipeline is powered by [Pipecat](https://github.com/pipecat-ai/pipecat), an open-source framework for building voice and multimodal conversational agents.

```text
Browser Microphone (PCM / WebRTC Audio)
                  │
                  ▼
       FastAPIWebsocketTransport
                  │
                  ▼
              Silero VAD
      (Voice Activity Detection)
                  │
                  ▼
            ElevenLabs STT
     (Conversational Transcription)
                  │
                  ▼
          Google Gemini LLM
    (Gemini 2.0 Flash + Tools)
                  │
     ┌────────────┴────────────┐
     ▼                         ▼
Direct Answer           Function Calling
                  (check_doctor_availability,
                   book_appointment,
                   cancel_appointment)
                               │
                               ▼
                        Shared Services
                               │
                               ▼
                        SQLite Database
                               │
                               ▼
                       Tool Result Frame
                               │
                               ▼
            ElevenLabs TTS
     (Ultra-Low-Latency Synthesis)
                  │
                  ▼
       FastAPIWebsocketTransport
                  │
                  ▼
        Browser Audio Output
```

---

## 2. Pipeline Components

### 2.1 Transport Layer (`FastAPIWebsocketTransport`)
- Receives raw PCM or WAV audio frames from the browser microphone over WebSocket (`/ws/call/{session_id}`).
- Emits synthesized audio binary chunks back to the browser for direct Web Audio API playback.

### 2.2 Voice Activity Detection (`SileroVADAnalyzer`)
- Uses ONNX runtime with Silero VAD to detect speech start, voice boundaries, and user pauses.
- Fires `UserStartedSpeakingFrame` (state -> `LISTENING`) and `UserStoppedSpeakingFrame` (state -> `THINKING`).
- Enables natural turn-taking without needing push-to-talk.

### 2.3 Speech-to-Text (`ElevenLabsSTTService`)
- Real-time streaming transcription model (`scribe_v1`).
- Accurately captures medical terms, doctor names, natural dates, and spoken digit sequences.

### 2.4 Language Model & Reasoning (`GoogleLLMService`)
- Model: `gemini-2.0-flash`.
- System Instruction: Healthcare receptionist persona enforcing patient phone read-back and confirmation separation.
- Registered Functions:
  1. `check_doctor_availability`
  2. `book_appointment`
  3. `cancel_appointment`

### 2.5 Text-to-Speech (`ElevenLabsTTSService`)
- Model: `eleven_turbo_v2_5`.
- Voice: Warm healthcare receptionist voice (`21m00Tcm4TlvDq8ikWAM` - Rachel).
- Low first-byte latency streaming audio generation.

---

## 3. Tool Calling Implementation

Tools are declared using `FunctionSchema` and registered with `llm.register_function(name, handler)`:

```python
AVAILABILITY_TOOL_SCHEMA = FunctionSchema(
    name="check_doctor_availability",
    description="Check doctor availability and return actual available appointment slots...",
    properties={
        "doctor_name": {"type": "string"},
        "speciality": {"type": "string"},
        "requested_date": {"type": "string"},
        "preferred_time": {"type": "string"}
    },
    required=[]
)
```

When Gemini invokes a tool, Pipecat calls the asynchronous handler:
```python
async def handle_check_doctor_availability(params: FunctionCallParams):
    args = params.arguments
    result = AppointmentService.check_doctor_availability(...)
    await params.result_callback(result)
```
The result is injected into the LLM context, which then synthesizes the natural spoken reply.
