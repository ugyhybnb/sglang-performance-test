#!/usr/bin/env python3
import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
import numpy as np
from transformers import AutoTokenizer


@dataclass
class MixedRequest:
    request_id: int
    request_type: str
    prompt: str
    prompt_len: int
    output_len: int


def generate_prompt(tokenizer: Any, token_num: int) -> str:
    vocab = list(tokenizer.get_vocab().values())
    token_ids = random.choices(vocab, k=token_num)
    return tokenizer.decode(token_ids)


def build_requests(tokenizer: Any, seed: int) -> list[MixedRequest]:
    random.seed(seed)
    requests: list[MixedRequest] = []
    request_id = 0

    def add(request_type: str, prompt_len: int, output_len: int, count: int) -> None:
        nonlocal request_id
        for _ in range(count):
            prompt = generate_prompt(tokenizer, prompt_len)
            requests.append(
                MixedRequest(request_id, request_type, prompt, prompt_len, output_len)
            )
            request_id += 1

    add("short_qa", 256, 64, 12)
    add("long_prompt", 4096, 64, 8)
    add("long_output", 512, 256, 8)

    shared_prefixes = [generate_prompt(tokenizer, 1024) for _ in range(4)]
    for group_id, prefix in enumerate(shared_prefixes):
        for _ in range(4):
            question = generate_prompt(tokenizer, 128)
            prompt = f"{prefix}\n\n{question}"
            prompt_len = len(tokenizer.encode(prompt))
            requests.append(
                MixedRequest(
                    request_id,
                    f"shared_prefix_g{group_id}",
                    prompt,
                    prompt_len,
                    128,
                )
            )
            request_id += 1

    random.shuffle(requests)
    return requests


async def send_one(
    session: aiohttp.ClientSession,
    url: str,
    model: str,
    req: MixedRequest,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": req.prompt}],
        "temperature": 0.0,
        "max_completion_tokens": req.output_len,
        "stream": True,
        "ignore_eos": True,
    }
    started = time.perf_counter()
    most_recent = started
    ttft = 0.0
    itls: list[float] = []
    chunks = 0
    generated_chars = 0
    error = ""
    success = False

    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = f"HTTP {response.status}: {await response.text()}"
            else:
                async for raw in response.content:
                    raw = raw.strip()
                    if not raw:
                        continue
                    text = raw.decode("utf-8")
                    if text.startswith("data: "):
                        text = text[len("data: ") :]
                    if text == "[DONE]":
                        continue
                    data = json.loads(text)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content") or ""
                    if not content:
                        continue
                    now = time.perf_counter()
                    if ttft == 0.0:
                        ttft = now - started
                    else:
                        itls.append(now - most_recent)
                    most_recent = now
                    chunks += 1
                    generated_chars += len(content)
                success = True
    except Exception as exc:  # noqa: BLE001
        error = repr(exc)

    latency = time.perf_counter() - started
    return {
        "kind": "request",
        "request_id": req.request_id,
        "request_type": req.request_type,
        "prompt_len": req.prompt_len,
        "output_len": req.output_len,
        "success": success,
        "latency_s": latency,
        "ttft_s": ttft,
        "itl_s": itls,
        "chunks": chunks,
        "generated_chars": generated_chars,
        "error": error,
    }


async def run(args: argparse.Namespace) -> None:
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
    input_requests = build_requests(tokenizer, args.seed)
    timeout = aiohttp.ClientTimeout(total=6 * 60 * 60)

    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    tasks: list[asyncio.Task] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for req in input_requests:
            tasks.append(asyncio.create_task(send_one(session, args.url, args.model, req)))
            if args.request_rate != float("inf"):
                await asyncio.sleep(float(np.random.exponential(1.0 / args.request_rate)))

        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            with open(args.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

    duration = time.perf_counter() - started
    summary: dict[str, Any] = {
        "kind": "summary",
        "duration_s": duration,
        "request_rate": args.request_rate,
        "total_requests": len(results),
        "successful_requests": sum(1 for r in results if r["success"]),
        "request_throughput": sum(1 for r in results if r["success"]) / duration,
        "by_type": {},
    }

    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["request_type"], []).append(result)

    for request_type, items in sorted(grouped.items()):
        ok = [x for x in items if x["success"]]
        latencies = [x["latency_s"] for x in ok]
        ttfts = [x["ttft_s"] for x in ok]
        itls = [v for x in ok for v in x["itl_s"]]
        summary["by_type"][request_type] = {
            "count": len(items),
            "success": len(ok),
            "p50_ttft_ms": float(np.percentile(ttfts, 50) * 1000) if ttfts else 0,
            "p99_ttft_ms": float(np.percentile(ttfts, 99) * 1000) if ttfts else 0,
            "p50_e2e_ms": float(np.percentile(latencies, 50) * 1000) if latencies else 0,
            "p99_e2e_ms": float(np.percentile(latencies, 99) * 1000) if latencies else 0,
            "mean_itl_ms": float(np.mean(itls) * 1000) if itls else 0,
        }

    with open(args.output_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:30000/v1/chat/completions")
    parser.add_argument("--model", default="Qwen3-14B")
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--request-rate", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
