#!/usr/bin/env python3
import csv
import json
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

OUT = Path("/home/dell/Kuiperinfer/projectA_v2")
JSONL = OUT / "jsonl"
METRICS = OUT / "metrics"
RAW = OUT / "figures" / "raw"
FINAL = OUT / "figures" / "final"


def read_result(stem: str) -> dict:
    path = JSONL / f"{stem}.jsonl"
    return json.loads(path.read_text().splitlines()[-1])


def savefig(name: str) -> None:
    for folder in (RAW, FINAL):
        folder.mkdir(parents=True, exist_ok=True)
        plt.savefig(folder / name, dpi=160, bbox_inches="tight")
    plt.close()


def write_csv(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    path = RAW / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_request_rate() -> None:
    stems = ["rr0_5_stream", "rr1_stream", "rr2_stream", "rr4_stream", "rr8_stream"]
    rows = []
    for stem in stems:
        d = read_result(stem)
        rows.append(
            {
                "scenario": stem,
                "request_rate": float(d["request_rate"]),
                "request_throughput": d["request_throughput"],
                "output_throughput": d["output_throughput"],
                "p99_e2e_latency_ms": d["p99_e2e_latency_ms"],
                "median_ttft_ms": d["median_ttft_ms"],
                "p99_ttft_ms": d["p99_ttft_ms"],
            }
        )
    write_csv("request_rate_summary.csv", rows)
    x = [r["request_rate"] for r in rows]

    plt.figure(figsize=(7, 4))
    plt.plot(x, [r["request_throughput"] for r in rows], marker="o", label="req/s")
    plt.plot(x, [r["output_throughput"] for r in rows], marker="s", label="output tok/s")
    plt.xlabel("Request rate")
    plt.ylabel("Throughput")
    plt.title("Qwen3-14B tp=4 Throughput vs Request Rate")
    plt.legend()
    plt.grid(True, alpha=0.3)
    savefig("throughput_vs_request_rate.png")

    plt.figure(figsize=(7, 4))
    plt.plot(x, [r["p99_e2e_latency_ms"] for r in rows], marker="o", color="#c44e52")
    plt.xlabel("Request rate")
    plt.ylabel("P99 E2E latency (ms)")
    plt.title("P99 E2E Latency vs Request Rate")
    plt.grid(True, alpha=0.3)
    savefig("p99_vs_request_rate.png")

    plt.figure(figsize=(7, 4))
    plt.plot(x, [r["median_ttft_ms"] for r in rows], marker="o", label="p50 TTFT")
    plt.plot(x, [r["p99_ttft_ms"] for r in rows], marker="s", label="p99 TTFT")
    plt.xlabel("Request rate")
    plt.ylabel("TTFT (ms)")
    plt.title("TTFT vs Request Rate")
    plt.legend()
    plt.grid(True, alpha=0.3)
    savefig("ttft_vs_request_rate.png")


def plot_long_prompt_output() -> None:
    prompt_stems = [f"long_prompt_{x}_stream" for x in [512, 2048, 4096, 8192]]
    prompt_rows = []
    for stem in prompt_stems:
        d = read_result(stem)
        prompt_rows.append(
            {
                "input_len": d["random_input_len"],
                "median_ttft_ms": d["median_ttft_ms"],
                "p99_ttft_ms": d["p99_ttft_ms"],
                "p99_e2e_latency_ms": d["p99_e2e_latency_ms"],
            }
        )
    write_csv("long_prompt_summary.csv", prompt_rows)
    x = [r["input_len"] for r in prompt_rows]
    plt.figure(figsize=(7, 4))
    plt.plot(x, [r["median_ttft_ms"] for r in prompt_rows], marker="o", label="p50 TTFT")
    plt.plot(x, [r["p99_ttft_ms"] for r in prompt_rows], marker="s", label="p99 TTFT")
    plt.xlabel("Prompt length (tokens)")
    plt.ylabel("TTFT (ms)")
    plt.title("Long Prompt TTFT")
    plt.legend()
    plt.grid(True, alpha=0.3)
    savefig("long_prompt_ttft.png")

    output_stems = [f"long_output_{x}_stream" for x in [64, 128, 256]]
    output_rows = []
    for stem in output_stems:
        d = read_result(stem)
        output_rows.append(
            {
                "output_len": d["random_output_len"],
                "median_e2e_latency_ms": d["median_e2e_latency_ms"],
                "p99_e2e_latency_ms": d["p99_e2e_latency_ms"],
                "mean_tpot_ms": d["mean_tpot_ms"],
            }
        )
    write_csv("long_output_summary.csv", output_rows)
    x = [r["output_len"] for r in output_rows]
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(x, [r["median_e2e_latency_ms"] for r in output_rows], marker="o", label="p50 E2E")
    ax1.plot(x, [r["p99_e2e_latency_ms"] for r in output_rows], marker="s", label="p99 E2E")
    ax1.set_xlabel("Output length (tokens)")
    ax1.set_ylabel("E2E latency (ms)")
    ax2 = ax1.twinx()
    ax2.plot(x, [r["mean_tpot_ms"] for r in output_rows], marker="^", color="#55a868", label="mean TPOT")
    ax2.set_ylabel("TPOT (ms)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")
    ax1.grid(True, alpha=0.3)
    plt.title("Long Output E2E and TPOT")
    savefig("long_output_e2e_tpot.png")


def plot_shared_prefix() -> None:
    rows = []
    for stem in ["random1152_rr4_stream", "gsp1024_rr4_stream"]:
        d = read_result(stem)
        rows.append(
            {
                "scenario": stem,
                "workload": "shared-prefix" if stem.startswith("gsp") else "random",
                "request_throughput": d["request_throughput"],
                "output_throughput": d["output_throughput"],
                "median_e2e_latency_ms": d["median_e2e_latency_ms"],
            }
        )
    cache_rows = []
    for stem in ["random1152_rr4_nonstream", "gsp1024_rr4_nonstream"]:
        d = read_result(stem)
        cache_rows.append(
            {
                "workload": "shared-prefix" if stem.startswith("gsp") else "random",
                "cache_hit_token_ratio": d["cache_hit_token_ratio"],
                "total_cached_tokens": d["total_cached_tokens"],
            }
        )
    write_csv("shared_prefix_summary.csv", rows + cache_rows)

    labels = [r["workload"] for r in rows]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, [r["output_throughput"] for r in rows], color=["#4c72b0", "#55a868"])
    plt.ylabel("Output throughput (tok/s)")
    plt.title("Shared Prefix Throughput Benefit")
    plt.grid(axis="y", alpha=0.3)
    savefig("shared_prefix_throughput.png")

    labels = [r["workload"] for r in cache_rows]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, [r["cache_hit_token_ratio"] for r in cache_rows], color=["#4c72b0", "#55a868"])
    plt.ylabel("Cache hit token ratio")
    plt.title("Shared Prefix Cache Hit Ratio")
    plt.grid(axis="y", alpha=0.3)
    savefig("shared_prefix_cache_hit_ratio.png")


def read_gpu(stem: str) -> list[dict]:
    path = METRICS / f"{stem}_gpu.csv"
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean = {k.strip(): v.strip() for k, v in row.items()}
            clean["timestamp_dt"] = datetime.strptime(clean["timestamp"], "%Y/%m/%d %H:%M:%S.%f")
            clean["seconds"] = (clean["timestamp_dt"] - rows[0]["timestamp_dt"]).total_seconds() if rows else 0
            clean["memory.used [MiB]"] = float(clean["memory.used [MiB]"])
            clean["utilization.gpu [%]"] = float(clean["utilization.gpu [%]"])
            clean["index"] = int(clean["index"])
            rows.append(clean)
    return rows


def read_queue(stem: str) -> list[dict]:
    rows = []
    current_t = None
    ts_re = re.compile(r"^# timestamp (.+)$")
    val_re = re.compile(r"^sglang:(num_running_reqs|num_queue_reqs)\\{.*\\} ([0-9.]+)$")
    for line in (METRICS / f"{stem}_metrics.prom").read_text().splitlines():
        m = ts_re.match(line)
        if m:
            current_t = len(rows)
            rows.append({"sample": current_t, "running": None, "queue": None})
            continue
        m = val_re.match(line)
        if m and rows:
            if m.group(1) == "num_running_reqs":
                rows[-1]["running"] = float(m.group(2))
            else:
                rows[-1]["queue"] = float(m.group(2))
    return [r for r in rows if r["running"] is not None or r["queue"] is not None]


def plot_stability() -> None:
    for metric, ylabel, name in [
        ("memory.used [MiB]", "GPU memory used (MiB)", "gpu_memory_stability.png"),
        ("utilization.gpu [%]", "GPU utilization (%)", "gpu_utilization_stability.png"),
    ]:
        plt.figure(figsize=(8, 4))
        for stem, prefix in [("stability_mid_rr4_30m", "mid"), ("stability_high_rr8_15m", "high")]:
            rows = read_gpu(stem)
            for idx in sorted({r["index"] for r in rows}):
                series = [r for r in rows if r["index"] == idx]
                plt.plot(
                    [r["seconds"] / 60 for r in series],
                    [r[metric] for r in series],
                    label=f"{prefix} gpu{idx}",
                    alpha=0.85,
                )
        plt.xlabel("Elapsed time (min)")
        plt.ylabel(ylabel)
        plt.title(ylabel + " During Stability Runs")
        plt.legend(ncol=4, fontsize=8)
        plt.grid(True, alpha=0.3)
        savefig(name)

    plt.figure(figsize=(8, 4))
    for stem, label in [("stability_mid_rr4_30m", "mid rr4"), ("stability_high_rr8_15m", "high rr8")]:
        rows = read_queue(stem)
        plt.plot([r["sample"] for r in rows], [r.get("running") or 0 for r in rows], label=f"{label} running")
        plt.plot([r["sample"] for r in rows], [r.get("queue") or 0 for r in rows], linestyle="--", label=f"{label} queue")
    plt.xlabel("Sample")
    plt.ylabel("Requests")
    plt.title("Running and Queued Requests During Stability Runs")
    plt.legend()
    plt.grid(True, alpha=0.3)
    savefig("queue_running_stability.png")

    rows = []
    for stem, label in [("stability_mid_rr4_30m", "mid rr4"), ("stability_high_rr8_15m", "high rr8")]:
        d = read_result(stem)
        rows.append(
            {
                "label": label,
                "request_throughput": d["request_throughput"],
                "p99_e2e_latency_ms": d["p99_e2e_latency_ms"],
                "p99_ttft_ms": d["p99_ttft_ms"],
            }
        )
    write_csv("stability_summary.csv", rows)
    x = [r["label"] for r in rows]
    plt.figure(figsize=(7, 4))
    plt.bar(x, [r["p99_e2e_latency_ms"] for r in rows], color=["#4c72b0", "#c44e52"])
    plt.ylabel("P99 E2E latency (ms)")
    plt.title("Stability Run P99 E2E Latency")
    plt.grid(axis="y", alpha=0.3)
    savefig("stability_p99_e2e.png")


def main() -> None:
    plot_request_rate()
    plot_long_prompt_output()
    plot_shared_prefix()
    plot_stability()


if __name__ == "__main__":
    main()
