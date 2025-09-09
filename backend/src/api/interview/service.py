import os
import subprocess
from typing import Tuple
import logging
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...models.models import Meeting, JobApplication, MeetingStatusEnum, Interview

logger = logging.getLogger(__name__)


VIDEOSDK_BASE_URL = os.getenv("VIDEOSDK_BASE_URL", "https://api.videosdk.live/v2")
VIDEOSDK_TIMEOUT = float(os.getenv("VIDEOSDK_TIMEOUT", "30"))
VIDEOSDK_INSECURE = os.getenv("VIDEOSDK_INSECURE", "false").lower() in ("1", "true", "yes")
VIDEOSDK_TOKEN = os.getenv("VIDEOSDK_AUTH_TOKEN", "")


def _headers_bearer() -> dict:
    if not VIDEOSDK_TOKEN:
        raise ValueError("VIDEOSDK_AUTH_TOKEN is not set")
    token = VIDEOSDK_TOKEN.strip()
    token = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    return {"Authorization": token, "Content-Type": "application/json"}


def _headers_raw_auth() -> dict:
    if not VIDEOSDK_TOKEN:
        raise ValueError("VIDEOSDK_AUTH_TOKEN is not set")
    return {"Authorization": VIDEOSDK_TOKEN.strip(), "Content-Type": "application/json"}


def _headers_x_api_key() -> dict:
    if not VIDEOSDK_TOKEN:
        raise ValueError("VIDEOSDK_AUTH_TOKEN is not set")
    return {"x-api-key": VIDEOSDK_TOKEN.strip(), "Content-Type": "application/json"}


def create_videosdk_room() -> Tuple[str, str]:
    """Create a VideoSDK room and return (room_id, join_link)."""
    with httpx.Client(timeout=VIDEOSDK_TIMEOUT, verify=not VIDEOSDK_INSECURE) as client:
        last_err = None
        try:
            resp = client.post(f"{VIDEOSDK_BASE_URL}/rooms", headers=_headers_raw_auth(), json={})
            resp.raise_for_status()
        except Exception as e:
            last_err = e
            resp = None  # type: ignore
        if resp is None:
            raise RuntimeError(f"VideoSDK room create failed: {last_err}")
        data = resp.json()
        room_id = data.get("roomId") or data.get("id") or data.get("room_id")
        if not room_id:
            raise RuntimeError("Failed to obtain roomId from VideoSDK response")
        # Build a set of candidate join links documented/observed
        playground = f"https://playground.videosdk.live/?token={VIDEOSDK_TOKEN}&meetingId={room_id}"
        logger.info(f"VideoSDK room created: id={room_id}, auth_scheme=raw_auth")
        return room_id, playground


def persist_meeting_for_application(db: Session, job_application_id: int, room_id: str, join_link: str) -> Meeting:
    job_application = db.query(JobApplication).filter_by(id=job_application_id).first()
    if not job_application:
        raise ValueError("Job application not found")

    meeting = Meeting(
        application_id=job_application.id,
        vacancy_id=job_application.vacancy_id,
        status="waitMeeting",
        hrContact="",
        meetLink=join_link,
        calendarLink="",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def start_agent_process(room_id: str) -> int:
    """Spawn ML agent process with ROOM_ID in env. Returns PID."""
    # Use agent code located inside backend image so it is available in container
    ml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/videosdk-examples"))
    entry = os.path.join(ml_dir, "main.py")
    env = os.environ.copy()
    env["ROOM_ID"] = room_id
    # Propagate tokens if needed
    if VIDEOSDK_TOKEN:
        env["VIDEOSDK_AUTH_TOKEN"] = VIDEOSDK_TOKEN
    # Forward optional model provider keys
    if os.getenv("GROQ_API_KEY"):
        env["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("CARTESIA_API_KEY"):
        env["CARTESIA_API_KEY"] = os.getenv("CARTESIA_API_KEY")
    # Start in background
    proc = subprocess.Popen(["python", entry], cwd=ml_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.pid


def save_interview_results(
    db: Session,
    job_application_id: int,
    summary: str,
    strengths: list[str],
    weaknesses: list[str],
    recommendations: str,
    verdict: str,
) -> Interview:
    job_application = db.query(JobApplication).filter_by(id=job_application_id).first()
    if not job_application:
        raise ValueError("Job application not found")

    interview = Interview(
        job_application_id=job_application.id,
        history_json="{}",
        feedback_json=recommendations,
        strengths=strengths,
        weaknesses=weaknesses,
        verdict=verdict,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview