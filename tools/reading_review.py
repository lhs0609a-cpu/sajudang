"""Export 30 synthetic comparison readings and a blank human-review worksheet.

Run: python tools/reading_review.py --out <directory>
No generated score is presented as a human rating or prediction accuracy.
"""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
from engine import interpretation as ip, reading_quality
from engine.report import build_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "reading-review")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    metrics = reading_quality.measure()
    (args.out / "checks.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), "utf-8")
    dataset = reading_quality.cases()
    domains = list(ip.content()["domains"])
    pages, answer_key = [], []
    with (args.out / "human-review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "reviewer", "role_expert_or_customer", "preferred_A_B_tie", "grounding_1_5", "specificity_1_5", "consistency_1_5", "actionability_1_5", "quoted_price", "would_pay_yes_no", "incorrect_claim_id", "notes"])
        for index, case in enumerate(dataset["cases"]):
            concern = domains[index % len(domains)]
            f = reading_quality.features(case, dataset["as_of"])
            plan = ip.build_plan(f, concern)
            reading = ip.render(plan, f, "all")
            modern = "".join("<h3>" + escape(row["title"]) + "</h3>" + row["html"] for row in reading["summary"] + reading["sections"])
            old = build_report(f, case["id"], "pungun", "all", concern)
            legacy = "".join("<h3>" + escape(c["title"]) + "</h3>" + c["html"] for c in old["cuts"])
            variants = [modern, legacy] if index % 2 == 0 else [legacy, modern]
            answer_key.append({"case": case["id"], "new_variant": "A" if index % 2 == 0 else "B"})
            pages.append(f"<article><h2>{case['id']} · {ip.content()['domains'][concern]['label']}</h2><p>합성 사례 · {' '.join(p['gz'] for p in f.pillars)}</p>" +
                "".join(f"<details><summary>풀이 {name}</summary>{body}</details>" for name, body in zip(("A", "B"), variants)) + "</article>")
            writer.writerow([case["id"]] + [""] * 11)
    (args.out / "answer-key.json").write_text(json.dumps(answer_key, ensure_ascii=False, indent=2), "utf-8")
    html = '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>전체 풀이 비교 검토 30건</title><style>body{max-width:880px;margin:auto;padding:24px;font:17px/1.85 system-ui;background:#faf8f2;color:#28251f}article{border-top:1px solid #ccc;margin-top:40px}summary{padding:20px;cursor:pointer}p{margin:18px 0}h3{margin-top:32px}details{border:1px solid #ddd;padding:12px;margin:16px 0}</style><h1>합성 사례 30건 · 풀이 비교</h1><p>자동으로 만든 검토 자료입니다. 전문가·고객 평가 결과가 아닙니다. A/B 순서를 번갈아 배치했으며, 평가표와 버전 정답표는 별도 파일입니다. 실제 가격을 제시한 고객 검증은 동의한 참여자와 별도로 진행하세요.</p>' + "".join(pages) + '</html>'
    (args.out / "readings.html").write_text(html, "utf-8")
    print(json.dumps({"out": str(args.out), "passed": metrics["passed"], "cases": metrics["cases"], "reports": metrics["reports"], "errors": metrics["errors"]}, ensure_ascii=False))
    return 0 if metrics["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
