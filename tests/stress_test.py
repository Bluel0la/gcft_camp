import asyncio
import httpx
import random
import string
import logging
import time

URL = "https://gcft-camp.onrender.com/api/v1/register-number"

# ---------------- Logging configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("stress-test")


# ---------------- Utilities ----------------
def random_phone():
    return "09" + "".join(random.choices(string.digits, k=8))


# ---------------- Shared counters ----------------
total_sent = 0
success_count = 0
failure_count = 0
lock = asyncio.Lock()


# ---------------- Request function ----------------
async def send_request(client):
    global total_sent, success_count, failure_count

    try:
        response = await client.post(
            URL,
            json={"phone_number": random_phone()},
            headers={"accept": "application/json"},
        )

        async with lock:
            total_sent += 1
            if 200 <= response.status_code < 300:
                success_count += 1
            else:
                failure_count += 1

    except Exception:
        async with lock:
            total_sent += 1
            failure_count += 1


# ---------------- Progress logger ----------------
async def log_progress(interval=1.0):
    start_time = time.monotonic()

    while True:
        await asyncio.sleep(interval)
        elapsed = time.monotonic() - start_time

        async with lock:
            logger.info(
                "Elapsed: %.1fs | Sent: %d | Success: %d | Failures: %d",
                elapsed,
                total_sent,
                success_count,
                failure_count,
            )


# ---------------- Stress test runner ----------------
async def stress_test(concurrency=1000):
    limits = httpx.Limits(
        max_connections=2000,
        max_keepalive_connections=500,
    )
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        logger_task = asyncio.create_task(log_progress())
        tasks = [send_request(client) for _ in range(concurrency)]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger_task.cancel()

        async with lock:
            logger.info(
                "FINAL RESULT → Sent: %d | Success: %d | Failures: %d",
                total_sent,
                success_count,
                failure_count,
            )


# ---------------- Entry point ----------------
asyncio.run(stress_test())
