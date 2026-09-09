"""Generate new animation from the exact shipped illustrations using fal's queue.

plan: offline source validation; submit: paid API calls; collect: resume/download.
Outputs remain in out/motion until visual review and encoding. Existing media is preserved.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps/web/public"
PLAN = ROOT / "seed/motion-production.json"
OUT = ROOT / "out/motion"
MODEL = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
VOICE_MODEL = "fal-ai/elevenlabs/tts/multilingual-v2"


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    temp.replace(path)


def source(job):
    if job["kind"] == "voice":
        return None, b""
    path = (PUBLIC / job["source"]).resolve()
    if not path.is_relative_to(PUBLIC.resolve()):
        raise ValueError("Source must be inside public")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != job["source_sha256"]:
        raise ValueError("Source changed: " + job["id"])
    return path, body


def fingerprint(job):
    model = VOICE_MODEL if job["kind"] == "voice" else MODEL
    return hashlib.sha256(json.dumps([model, job], sort_keys=True).encode()).hexdigest()


def queue_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "queue.fal.run":
        raise ValueError("Unexpected queue URL")
    return url


def submit(client, jobs, state, state_path):
    # Validate the entire selection before any paid request.
    for job in jobs:
        source(job)
        old = state.get(job["id"])
        if old and old["fingerprint"] != fingerprint(job):
            raise ValueError("Job changed after submission: " + job["id"])
    for job in jobs:
        if job["id"] in state:
            print(job["id"], "already recorded; no duplicate submission", flush=True)
            continue
        if job["kind"] == "voice":
            model = VOICE_MODEL
            payload = {"text": job["text"], "voice": job["voice"], "stability": 0.55,
                       "style": 0.15, "speed": 0.95, "output_format": "mp3_44100_128"}
        else:
            model = MODEL
            path, body = source(job)
            uri = "data:%s;base64,%s" % (mimetypes.guess_type(path.name)[0], base64.b64encode(body).decode())
            payload = {"image_url": uri, "prompt": job["prompt"], "duration": str(job["seconds"]),
                       "negative_prompt": "identity change, deformed face, extra fingers, text, watermark, camera shake, photorealism"}
            if job["loop"]:
                payload["tail_image_url"] = uri
        # A timeout can occur after acceptance: do not blindly retry paid POSTs.
        state[job["id"]] = {"fingerprint": fingerprint(job), "status": "submission_unconfirmed"}
        save(state_path, state)
        response = client.post("https://queue.fal.run/" + model, json=payload)
        response.raise_for_status()
        data = response.json()
        state[job["id"]].update(request_id=data["request_id"], status="submitted",
                                status_url=queue_url(data["status_url"]),
                                response_url=queue_url(data["response_url"]))
        save(state_path, state)
        print(job["id"], "submitted", flush=True)


def collect(client, jobs, state, state_path, out):
    for job in jobs:
        entry = state.get(job["id"], {})
        if not entry.get("status_url") or entry.get("status") == "downloaded":
            continue
        r = client.get(queue_url(entry["status_url"]))
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            entry["status"] = "failed"
            save(state_path, state)
            print(job["id"], "provider reported failure", flush=True)
            continue
        if data["status"] != "COMPLETED":
            print(job["id"], data["status"], flush=True)
            continue
        r = client.get(queue_url(entry["response_url"]))
        r.raise_for_status()
        is_voice = job["kind"] == "voice"
        url = r.json()["audio" if is_voice else "video"]["url"]
        if urlparse(url).scheme != "https":
            raise ValueError("Video URL must use HTTPS")
        target = out / (job["id"] + (".mp3" if is_voice else ".mp4"))
        # Separate client: NEVER send the API credential to the media host.
        with httpx.stream("GET", url, follow_redirects=True, timeout=120) as download:
            download.raise_for_status()
            count = 0
            with target.with_suffix(".part").open("wb") as f:
                for chunk in download.iter_bytes():
                    count += len(chunk)
                    if count > 150_000_000:
                        raise ValueError("Unexpectedly large media")
                    f.write(chunk)
        if count < 1024:
            raise ValueError("Invalid empty media")
        target.with_suffix(".part").replace(target)
        entry.update(status="downloaded", file=target.name, bytes=count, reviewed=False)
        save(state_path, state)
        print(job["id"], "downloaded; visual review pending", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "submit", "collect"])
    parser.add_argument("--id", action="append", help="Select jobs; otherwise select the full production list")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    production = json.loads(PLAN.read_text(encoding="utf8"))
    jobs = production["jobs"] + [{"id": "voice-pungun", "kind": "voice",
                                  "text": production["voice"]["text"],
                                  "voice": os.getenv("SJD_NARRATOR_VOICE", "George")}]
    if args.id:
        if set(args.id) - {j["id"] for j in jobs}:
            parser.error("Unknown job id")
        jobs = [j for j in jobs if j["id"] in args.id]
    for job in jobs:
        source(job)
    if args.command == "plan":
        print(json.dumps({"jobs": len(jobs), "video_seconds": sum(j.get("seconds", 0) for j in jobs),
                          "sources_verified": True, "credential_configured": bool(os.getenv("FAL_KEY"))}))
        return
    key = os.getenv("FAL_KEY", "").strip()
    if not key:
        parser.exit(2, "FAL_KEY is not configured. No generation requests were submitted.\n")
    args.out.mkdir(parents=True, exist_ok=True)
    lock = args.out / "generation.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        parser.exit(2, "A generation process owns this output folder.\n")
    try:
        os.close(fd)
        state_path = args.out / "jobs.json"
        state = json.loads(state_path.read_text(encoding="utf8")) if state_path.exists() else {}
        with httpx.Client(headers={"Authorization": "Key " + key}, timeout=60) as client:
            if args.command == "submit":
                submit(client, jobs, state, state_path)
            else:
                collect(client, jobs, state, state_path, args.out)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
