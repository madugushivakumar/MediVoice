import os
import json
import uuid
import wave
import io
import math
import struct
import asyncio
import logging
import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState
import aiohttp

from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    OutputAudioRawFrame,
    AudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    EndFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    LLMMessagesAppendFrame,
    ErrorFrame,
    FunctionCallResultFrame,
    FunctionCallsStartedFrame
)

from app.config.settings import settings
from app.services.event_service import event_service
from app.agents.conversation_state import ConversationState
from app.agents.doctor_assistant import DoctorAssistantAgent
from app.agents.system_prompt import get_system_prompt
from app.services.appointment_service import AppointmentService
from app.database.connection import SessionLocal

logger = logging.getLogger("medivoice.pipeline")
voice_router = APIRouter()

active_call_states: Dict[str, ConversationState] = {}

def generate_tone_wav(duration_secs: float = 0.5, freq: float = 440.0, sample_rate: int = 16000) -> bytes:
    """Helper to generate a clean synthetic sine audio WAV frame for browser audio playback."""
    num_samples = int(duration_secs * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            env = min(1.0, i / 200.0) * min(1.0, (num_samples - i) / 200.0)
            sample = int(32767.0 * 0.3 * env * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        wf.writeframes(frames)
    return buffer.getvalue()

async def synthesize_elevenlabs_pcm(text: str) -> Optional[bytes]:
    """
    Direct ElevenLabs HTTP Text-to-Speech synthesis helper.
    Returns 16kHz raw PCM bytes, or None if unavailable or on error.
    """
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        return None

    voice_id = settings.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
    model_id = settings.ELEVENLABS_TTS_MODEL or "eleven_turbo_v2_5"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_16000"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logger.warning(f"ElevenLabs HTTP TTS returned status {resp.status}")
    except Exception as e:
        logger.warning(f"Failed to synthesize ElevenLabs TTS: {e}")
    return None

class MediVoiceFrameSerializer(FrameSerializer):
    """
    Bidirectional FrameSerializer for MediVoice:
    - Deserializes incoming browser 16-bit 16kHz PCM audio bytes into InputAudioRawFrame.
    - Deserializes incoming JSON control messages into frames.
    - Serializes outgoing OutputAudioRawFrame to audio bytes for browser playback.
    """
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, (OutputAudioRawFrame, AudioRawFrame)):
            return frame.audio
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes):
            # Raw PCM 16-bit 16kHz mono audio from browser microphone
            return InputAudioRawFrame(audio=data, num_channels=1, sample_rate=16000)
        elif isinstance(data, str):
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")
                if msg_type == "END_CALL":
                    return EndFrame()
                elif msg_type in ("USER_SPEECH", "MESSAGE"):
                    text = msg.get("text", "").strip()
                    if text:
                        return LLMMessagesAppendFrame(
                            messages=[{"role": "user", "content": text}],
                            run_llm=True
                        )
            except Exception:
                pass
        return None

class IngressObserverProcessor(FrameProcessor):
    """
    Observes incoming user control frames immediately after transport.input()
    to ensure typed messages and simulated quick prompts update the conversation state,
    render in the frontend live transcript as Caller bubbles, and transition state to THINKING
    before Pipecat's context aggregator processes them.
    """
    def __init__(self, websocket: WebSocket, session_id: str, conv_state: ConversationState):
        super().__init__()
        self.websocket = websocket
        self.session_id = session_id
        self.conv_state = conv_state

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        try:
            if isinstance(frame, LLMMessagesAppendFrame):
                for m in frame.messages:
                    if m.get("role") == "user":
                        text = m.get("content", "").strip()
                        if text:
                            logger.info(f"[{self.session_id}] Caller typed/quick prompt: {text}")
                            self.conv_state.add_message("Caller", text)
                            self.conv_state.set_status("THINKING")
                            if self.websocket.client_state == WebSocketState.CONNECTED:
                                await self.websocket.send_text(json.dumps({
                                    "type": "TRANSCRIPT_UPDATE",
                                    "data": {
                                        "session_id": self.session_id,
                                        "speaker": "Caller",
                                        "message": text,
                                        "timestamp": datetime.datetime.utcnow().isoformat(),
                                        "status": "final"
                                    }
                                }))
                                await self.websocket.send_text(json.dumps({
                                    "type": "CALL_STATE_CHANGED",
                                    "data": {"session_id": self.session_id, "state": "THINKING"}
                                }))
        except Exception as e:
            logger.warning(f"Error in IngressObserverProcessor: {e}")

        await self.push_frame(frame, direction)

class EventObserverProcessor(FrameProcessor):
    """
    Observes pipeline frames to record conversation history in the database
    and broadcast live events (transcripts, state transitions, tool calls) to the frontend.
    """
    def __init__(self, websocket: WebSocket, session_id: str, conv_state: ConversationState):
        super().__init__()
        self.websocket = websocket
        self.session_id = session_id
        self.conv_state = conv_state

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        try:
            if isinstance(frame, BotStartedSpeakingFrame):
                logger.info(f"[{self.session_id}] AI speaking")
                self.conv_state.set_status("SPEAKING")
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    await self.websocket.send_text(json.dumps({
                        "type": "CALL_STATE_CHANGED",
                        "data": {"session_id": self.session_id, "state": "SPEAKING"}
                    }))
            elif isinstance(frame, BotStoppedSpeakingFrame):
                logger.info(f"[{self.session_id}] AI finished speaking")
                self.conv_state.set_status("CONNECTED")
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    await self.websocket.send_text(json.dumps({
                        "type": "CALL_STATE_CHANGED",
                        "data": {"session_id": self.session_id, "state": "CONNECTED"}
                    }))
            elif isinstance(frame, FunctionCallsStartedFrame):
                logger.info(f"[{self.session_id}] Function call started: {[fc.function_name for fc in frame.function_calls]}")
                self.conv_state.set_status("THINKING")
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    await self.websocket.send_text(json.dumps({
                        "type": "CALL_STATE_CHANGED",
                        "data": {"session_id": self.session_id, "state": "THINKING"}
                    }))
            elif isinstance(frame, FunctionCallResultFrame):
                tool_name = getattr(frame, "function_name", "tool")
                tool_res = getattr(frame, "result", {})
                logger.info(f"[{self.session_id}] Function call result for {tool_name}")
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    await self.websocket.send_text(json.dumps({
                        "type": "TOOL_EXECUTED",
                        "data": {
                            "tool": tool_name,
                            "result": tool_res
                        }
                    }))
            elif isinstance(frame, ErrorFrame):
                err = getattr(frame, "error", "Voice pipeline error")
                logger.error(f"[{self.session_id}] Pipeline error frame: {err}")
                self.conv_state.set_status("ERROR")
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    await self.websocket.send_text(json.dumps({
                        "type": "CALL_STATE_CHANGED",
                        "data": {"session_id": self.session_id, "state": "ERROR", "error": str(err)}
                    }))
        except Exception as e:
            logger.warning(f"Error observing pipeline frame: {e}")

        await self.push_frame(frame, direction)

@voice_router.post("/api/calls/start")
def start_call_session():
    """Generates a new call session ID for the voice assistant."""
    session_id = f"call_{uuid.uuid4().hex[:12]}"
    conv_state = ConversationState(session_id)
    active_call_states[session_id] = conv_state
    logger.info(f"Initialized call session {session_id}")
    return {
        "session_id": session_id,
        "status": "CONNECTING",
        "created_at": conv_state.started_at.isoformat()
    }

@voice_router.post("/api/calls/{session_id}/end")
def end_call_session(session_id: str):
    """Terminates a call session and persists the duration."""
    state = active_call_states.get(session_id)
    if state:
        state.end_call()
        active_call_states.pop(session_id, None)
    return {"session_id": session_id, "status": "ENDED"}

@voice_router.websocket("/ws/call/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"Voice WebSocket connected for session {session_id}")

    conv_state = active_call_states.get(session_id)
    if not conv_state:
        conv_state = ConversationState(session_id)
        active_call_states[session_id] = conv_state

    conv_state.set_status("CONNECTED")
    await websocket.send_text(json.dumps({
        "type": "CALL_STATE_CHANGED",
        "data": {"session_id": session_id, "state": "CONNECTED"}
    }))

    # Determine whether cloud API keys are present
    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")
    has_elevenlabs = bool(settings.ELEVENLABS_API_KEY and settings.ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here")
    use_live_cloud_pipeline = has_gemini and has_elevenlabs and not os.environ.get("TESTING")

    # Inform frontend of the active pipeline mode
    pipeline_mode = "LIVE_VOICE" if use_live_cloud_pipeline else "TEXT_FALLBACK"
    await websocket.send_text(json.dumps({
        "type": "PIPELINE_MODE",
        "data": {
            "mode": pipeline_mode,
            "has_gemini": has_gemini,
            "has_elevenlabs": has_elevenlabs
        }
    }))

    # Initial greeting from MediVoice Assistant
    greeting_text = "Hello! Welcome to MediVoice Healthcare Clinic. How may I assist you with your appointment today?"
    conv_state.add_message(speaker="AI", message=greeting_text)
    
    await websocket.send_text(json.dumps({
        "type": "TRANSCRIPT_UPDATE",
        "data": {
            "session_id": session_id,
            "speaker": "AI",
            "message": greeting_text,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "status": "final"
        }
    }))

    if has_elevenlabs and not os.environ.get("TESTING"):
        greeting_audio = await synthesize_elevenlabs_pcm(greeting_text)
        if greeting_audio and websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_bytes(greeting_audio)

    if use_live_cloud_pipeline:
        logger.info(f"Starting real-time Pipecat pipeline with Gemini & ElevenLabs for {session_id}")
        await _run_pipecat_pipeline(websocket, session_id, conv_state, greeting_text=greeting_text)
    else:
        logger.info(f"Running conversational voice workflow engine for {session_id} (Cloud keys absent or dev mode)")
        await _run_conversational_workflow(websocket, session_id, conv_state, has_elevenlabs=has_elevenlabs)

async def _run_pipecat_pipeline(websocket: WebSocket, session_id: str, conv_state: ConversationState, greeting_text: str = ""):
    """
    Executes the genuine Pipecat pipeline with Gemini LLM, ElevenLabs STT & TTS,
    Silero VAD, context aggregation, and MediVoiceFrameSerializer.
    """
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.task import PipelineTask, PipelineParams
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
    from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.processors.audio.vad_processor import VADProcessor
    from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
    from pipecat.processors.aggregators.llm_context import LLMContext

    serializer = MediVoiceFrameSerializer(session_id=session_id)

    async with aiohttp.ClientSession() as aiohttp_session:
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                serializer=serializer,
                add_wav_header=False
            )
        )

        vad = VADProcessor(vad_analyzer=SileroVADAnalyzer())
        stt = ElevenLabsSTTService(
            api_key=settings.ELEVENLABS_API_KEY,
            aiohttp_session=aiohttp_session,
            sample_rate=16000,
            model=settings.ELEVENLABS_STT_MODEL
        )
        llm = DoctorAssistantAgent.create_llm_service()
        tts = ElevenLabsTTSService(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model=settings.ELEVENLABS_TTS_MODEL,
            sample_rate=16000
        )

        # Context aggregator pair for user speech and assistant responses
        initial_messages = [{"role": "system", "content": get_system_prompt()}]
        if greeting_text:
            initial_messages.append({"role": "assistant", "content": greeting_text})
        context = LLMContext(messages=initial_messages)
        context_pair = LLMContextAggregatorPair(context)

        # Wire turn lifecycle event handlers for real-time frontend transcript & state sync
        @context_pair.user().event_handler("on_user_turn_started")
        async def on_user_speaking(_aggregator, _strategy):
            logger.info(f"[{session_id}] Caller started speaking -> LISTENING")
            conv_state.set_status("LISTENING")
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps({
                    "type": "CALL_STATE_CHANGED",
                    "data": {"session_id": session_id, "state": "LISTENING"}
                }))

        @context_pair.user().event_handler("on_user_turn_stopped")
        async def on_user_stopped(_aggregator, _strategy, _message):
            logger.info(f"[{session_id}] Caller finished speaking -> THINKING")
            conv_state.set_status("THINKING")
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps({
                    "type": "CALL_STATE_CHANGED",
                    "data": {"session_id": session_id, "state": "THINKING"}
                }))

        @context_pair.user().event_handler("on_user_turn_message_added")
        async def on_user_message(_aggregator, message):
            text = message.content.strip() if message.content else ""
            if text:
                logger.info(f"[{session_id}] STT transcribed caller speech: {text}")
                conv_state.add_message("Caller", text)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps({
                        "type": "TRANSCRIPT_UPDATE",
                        "data": {
                            "session_id": session_id,
                            "speaker": "Caller",
                            "message": text,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "status": "final"
                        }
                    }))

        @context_pair.assistant().event_handler("on_assistant_turn_stopped")
        async def on_assistant_message(_aggregator, message):
            text = message.content.strip() if message.content else ""
            if text:
                logger.info(f"[{session_id}] Gemini response completed: {text}")
                conv_state.add_message("AI", text)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps({
                        "type": "TRANSCRIPT_UPDATE",
                        "data": {
                            "session_id": session_id,
                            "speaker": "AI",
                            "message": text,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "status": "final"
                        }
                    }))

        # Frame observers: ingress for typed prompts, egress for speech/state/tools
        ingress_observer = IngressObserverProcessor(websocket, session_id, conv_state)
        observer = EventObserverProcessor(websocket, session_id, conv_state)

        pipeline = Pipeline([
            transport.input(),
            ingress_observer,
            vad,
            stt,
            context_pair.user(),
            llm,
            tts,
            transport.output(),
            context_pair.assistant(),
            observer
        ])

        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
        runner = PipelineRunner()

        try:
            await runner.run(task)
        except Exception as e:
            logger.error(f"Pipecat pipeline error in session {session_id}: {e}", exc_info=True)
        finally:
            conv_state.end_call()

async def _run_conversational_workflow(websocket: WebSocket, session_id: str, conv_state: ConversationState, has_elevenlabs: bool = False):
    """
    Conversational voice workflow engine for development, testing, and fallback.
    Processes browser audio bytes (calculates RMS energy for waveform feedback),
    manages call state (LISTENING, THINKING, SPEAKING), executes genuine appointment tools,
    enforces 10-digit spoken phone number readback and booking confirmation.
    """
    intent = None
    target_doctor = None
    target_date = None
    target_time = None
    target_slot_id = None
    spoken_phone = None
    phone_confirmed = False
    awaiting_phone_confirmation = False
    awaiting_booking_confirmation = False
    awaiting_cancellation_confirmation = False
    target_appointment_id = None
    notice_sent = False

    try:
        while True:
            message = await websocket.receive()

            # Handle incoming binary audio chunks from browser microphone
            if "bytes" in message:
                audio_bytes = message["bytes"]
                if len(audio_bytes) >= 2:
                    try:
                        shorts = struct.unpack(f"<{len(audio_bytes)//2}h", audio_bytes)
                        sum_sq = sum(s * s for s in shorts)
                        rms = math.sqrt(sum_sq / len(shorts)) / 32768.0

                        # If user is speaking aloud into microphone without cloud STT key, send notice once
                        if rms > 0.06 and not notice_sent:
                            notice_sent = True
                            await websocket.send_text(json.dumps({
                                "type": "VOICE_MODE_NOTICE",
                                "data": {
                                    "message": "Microphone audio signal active. To convert live speech to text via ElevenLabs STT, configure ELEVENLABS_API_KEY in voice-agent/.env. You can also use quick prompt buttons or typed input."
                                }
                            }))
                    except Exception:
                        pass
                continue

            # Handle text messages
            if "text" in message:
                try:
                    payload = json.loads(message["text"])
                    msg_type = payload.get("type")
                    text_content = payload.get("text", "").strip()

                    if msg_type == "END_CALL":
                        break
                    elif msg_type == "MUTE":
                        continue
                    elif msg_type in ("USER_SPEECH", "MESSAGE"):
                        if not text_content:
                            continue

                        # Caller spoken message received
                        conv_state.add_message("Caller", text_content)
                        await websocket.send_text(json.dumps({
                            "type": "TRANSCRIPT_UPDATE",
                            "data": {
                                "session_id": session_id,
                                "speaker": "Caller",
                                "message": text_content,
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "status": "final"
                            }
                        }))

                        # Transition to THINKING state
                        conv_state.set_status("THINKING")
                        await websocket.send_text(json.dumps({
                            "type": "CALL_STATE_CHANGED",
                            "data": {"session_id": session_id, "state": "THINKING"}
                        }))
                        await asyncio.sleep(0.4)

                        db = SessionLocal()
                        ai_reply = ""
                        tool_event = None

                        try:
                            lowered = text_content.lower()

                            # -------------------------------------------------------------
                            # STEP 1: Handle phone confirmation if pending
                            # -------------------------------------------------------------
                            if awaiting_phone_confirmation:
                                if any(word in lowered for word in ["yes", "correct", "right", "yeah", "yep", "true"]):
                                    phone_confirmed = True
                                    awaiting_phone_confirmation = False
                                    conv_state.confirmed_phone = spoken_phone

                                    if intent == "cancel":
                                        cancel_check = AppointmentService.cancel_appointment(
                                            db, patient_phone=spoken_phone, confirm_cancellation=False, session_id=session_id
                                        )
                                        if cancel_check.get("error") == "MULTIPLE_APPOINTMENTS":
                                            appts_summary = ", ".join([f"{a['doctor_name']} on {a['date']} at {a['time']} (ID: {a['appointment_id']})" for a in cancel_check["appointments"]])
                                            ai_reply = f"I found multiple appointments: {appts_summary}. Which appointment ID would you like to cancel?"
                                        elif cancel_check.get("error") == "CONFIRMATION_REQUIRED":
                                            awaiting_cancellation_confirmation = True
                                            ai_reply = cancel_check["message"]
                                        else:
                                            ai_reply = cancel_check.get("message", "Could not find any active appointments.")
                                    else:
                                        awaiting_booking_confirmation = True
                                        doc_display = target_doctor or "the selected doctor"
                                        date_display = target_date or "your selected date"
                                        time_display = target_time or "10:30 AM"
                                        ai_reply = f"You selected {doc_display} on {date_display} at {time_display}. Shall I confirm this appointment using your phone number ending in {spoken_phone[-4:]}?"
                                else:
                                    awaiting_phone_confirmation = False
                                    spoken_phone = None
                                    ai_reply = "I apologize for that. Please speak your 10-digit phone number again."

                            # -------------------------------------------------------------
                            # STEP 2: Handle Booking Authorization confirmation
                            # -------------------------------------------------------------
                            elif awaiting_booking_confirmation:
                                if any(word in lowered for word in ["yes", "confirm", "book", "proceed", "sure", "please"]):
                                    awaiting_booking_confirmation = False
                                    book_res = AppointmentService.book_appointment(
                                        db=db,
                                        patient_phone=spoken_phone,
                                        slot_id=target_slot_id,
                                        doctor_name=target_doctor,
                                        appointment_date=target_date,
                                        start_time=target_time,
                                        session_id=session_id
                                    )
                                    tool_event = {
                                        "tool": "book_appointment",
                                        "result": book_res
                                    }
                                    if book_res.get("success"):
                                        ai_reply = f"Your appointment has been successfully booked with {book_res['doctor_name']} for {book_res['appointment_date']} at {book_res['start_time']}. Your confirmation ID is {book_res['appointment_id']}."
                                    else:
                                        ai_reply = f"I could not complete the booking. {book_res.get('message', 'The requested slot is no longer available.')}"
                                else:
                                    awaiting_booking_confirmation = False
                                    ai_reply = "Understood. The appointment booking has not been confirmed. Would you like to select a different doctor or time?"

                            # -------------------------------------------------------------
                            # STEP 3: Handle Cancellation confirmation
                            # -------------------------------------------------------------
                            elif awaiting_cancellation_confirmation:
                                if any(word in lowered for word in ["yes", "cancel", "confirm", "proceed", "sure"]):
                                    awaiting_cancellation_confirmation = False
                                    cancel_res = AppointmentService.cancel_appointment(
                                        db=db,
                                        patient_phone=spoken_phone,
                                        appointment_id=target_appointment_id,
                                        confirm_cancellation=True,
                                        session_id=session_id
                                    )
                                    tool_event = {
                                        "tool": "cancel_appointment",
                                        "result": cancel_res
                                    }
                                    if cancel_res.get("success"):
                                        ai_reply = f"Your appointment has been successfully cancelled and the slot has been released. {cancel_res.get('message', '')}"
                                    else:
                                        ai_reply = f"Cancellation failed: {cancel_res.get('message', 'Please try again.')}"
                                else:
                                    awaiting_cancellation_confirmation = False
                                    ai_reply = "Understood. Your appointment remains scheduled."

                            # -------------------------------------------------------------
                            # STEP 4: Detect Cancellation Intent
                            # -------------------------------------------------------------
                            elif "cancel" in lowered:
                                intent = "cancel"
                                digits = AppointmentService.normalize_phone(text_content)
                                if len(digits) == 10 and AppointmentService.validate_phone(digits):
                                    spoken_phone = digits
                                    awaiting_phone_confirmation = True
                                    hyphenated = "-".join(list(digits))
                                    ai_reply = f"I heard {hyphenated}. Is that correct?"
                                else:
                                    ai_reply = "I can certainly help you cancel an appointment. Please tell me the 10-digit phone number used for the booking."

                            # -------------------------------------------------------------
                            # STEP 5: Detect Spoken Phone Number (10 digits)
                            # -------------------------------------------------------------
                            elif any(c.isdigit() for c in text_content) and len(AppointmentService.normalize_phone(text_content)) >= 10:
                                digits = AppointmentService.normalize_phone(text_content)
                                if len(digits) == 10 and AppointmentService.validate_phone(digits):
                                    spoken_phone = digits
                                    awaiting_phone_confirmation = True
                                    hyphenated = "-".join(list(digits))
                                    ai_reply = f"I heard {hyphenated}. Is that correct?"
                                else:
                                    ai_reply = "I heard a phone number, but it must be a valid 10-digit mobile number. Could you please repeat it?"

                            # -------------------------------------------------------------
                            # STEP 6: Detect Time Selection for Booking
                            # -------------------------------------------------------------
                            elif any(t in lowered for t in ["10:30", "11:30", "09:30", "9:30", "2:00", "2 pm", "02:00", "3:00", "03:00", "4:30", "04:30"]):
                                for t in ["09:30 AM", "10:30 AM", "11:30 AM", "02:00 PM", "03:00 PM", "04:30 PM"]:
                                    if t[:5].replace("0", "") in lowered or t[:5] in lowered:
                                        target_time = t
                                        break
                                ai_reply = f"Certainly! I have noted {target_time or 'your chosen time'}. May I have your 10-digit mobile number to proceed?"

                            # -------------------------------------------------------------
                            # STEP 7: Detect Doctor Availability Query
                            # -------------------------------------------------------------
                            elif any(word in lowered for word in ["available", "availability", "doctor", "cardiologist", "dermatologist", "neurologist", "orthopedic", "pediatrician", "slot", "appointment", "schedule"]):
                                spec = None
                                for s in ["cardiology", "dermatology", "neurology", "orthopedics", "pediatrics", "general medicine", "gynecology", "ent"]:
                                    if s in lowered or (s == "cardiology" and "cardiologist" in lowered) or (s == "dermatology" and "dermatologist" in lowered) or (s == "neurology" and "neurologist" in lowered) or (s == "pediatrics" and "pediatrician" in lowered):
                                        spec = s.capitalize()
                                        break
                                
                                doc_cand = None
                                for d in ["arjun", "priya", "rajesh", "ananya", "vikram", "sunita", "kavita", "rohan"]:
                                    if d in lowered:
                                        doc_cand = d
                                        break

                                req_date = "today"
                                if "tomorrow" in lowered:
                                    req_date = "tomorrow"
                                elif "day after" in lowered:
                                    req_date = "day after tomorrow"

                                pref_time = None
                                if "10:30" in lowered:
                                    pref_time = "10:30 AM"
                                elif "11:30" in lowered:
                                    pref_time = "11:30 AM"
                                elif "2" in lowered or "02:00" in lowered:
                                    pref_time = "02:00 PM"
                                elif "morning" in lowered:
                                    pref_time = "morning"
                                elif "afternoon" in lowered:
                                    pref_time = "afternoon"

                                avail_res = AppointmentService.check_doctor_availability(
                                    db=db,
                                    doctor_name=doc_cand,
                                    speciality=spec,
                                    requested_date=req_date,
                                    preferred_time=pref_time,
                                    session_id=session_id
                                )
                                tool_event = {
                                    "tool": "check_doctor_availability",
                                    "result": avail_res
                                }

                                if avail_res.get("success") and avail_res.get("available_slots"):
                                    first_doc = avail_res["doctors"][0]["name"]
                                    slots_for_first = [s for s in avail_res["available_slots"] if s["doctor_name"] == first_doc]
                                    sample_times = [s["start_time"] for s in slots_for_first[:3]]
                                    times_str = " and ".join(sample_times) if len(sample_times) <= 2 else f"{sample_times[0]}, {sample_times[1]}, and {sample_times[2]}"
                                    target_doctor = first_doc
                                    target_date = avail_res["date"]
                                    target_slot_id = slots_for_first[0]["slot_id"]
                                    target_time = slots_for_first[0]["start_time"]

                                    ai_reply = f"{first_doc} has appointments available on {target_date} at {times_str}. Which time would you prefer?"
                                else:
                                    ai_reply = f"I checked our schedule, but no appointments are available for that request. Would you like to check tomorrow or another speciality?"

                            else:
                                ai_reply = "I am here to help you with doctor availability, booking, and cancellations. Would you like to check available doctors or book an appointment?"

                        finally:
                            db.close()

                        # Emit Tool Execution event
                        if tool_event:
                            await websocket.send_text(json.dumps({
                                "type": "TOOL_EXECUTED",
                                "data": tool_event
                            }))

                        # Transition to SPEAKING state
                        conv_state.set_status("SPEAKING")
                        await websocket.send_text(json.dumps({
                            "type": "CALL_STATE_CHANGED",
                            "data": {"session_id": session_id, "state": "SPEAKING"}
                        }))

                        # Record and send AI transcript
                        conv_state.add_message("AI", ai_reply)
                        await websocket.send_text(json.dumps({
                            "type": "TRANSCRIPT_UPDATE",
                            "data": {
                                "session_id": session_id,
                                "speaker": "AI",
                                "message": ai_reply,
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "status": "final"
                            }
                        }))

                        # Send audio frame for browser output playback:
                        # Direct ElevenLabs TTS speech if API key configured, otherwise synthetic tone
                        audio_data = None
                        if has_elevenlabs and not os.environ.get("TESTING"):
                            audio_data = await synthesize_elevenlabs_pcm(ai_reply)
                        if not audio_data:
                            audio_data = generate_tone_wav(duration_secs=0.3, freq=520.0)
                        await websocket.send_bytes(audio_data)

                        # Return to CONNECTED (LISTENING) state
                        await asyncio.sleep(0.5)
                        conv_state.set_status("CONNECTED")
                        await websocket.send_text(json.dumps({
                            "type": "CALL_STATE_CHANGED",
                            "data": {"session_id": session_id, "state": "CONNECTED"}
                        }))

                except json.JSONDecodeError:
                    pass

    except (WebSocketDisconnect, Exception) as e:
        if isinstance(e, WebSocketDisconnect) or "disconnect" in str(e).lower():
            logger.info(f"Voice WebSocket disconnected for session {session_id}")
        else:
            logger.error(f"Error in voice websocket: {e}", exc_info=True)
    finally:
        conv_state.end_call()
        await event_service.broadcast("CALL_ENDED", {"session_id": session_id})
