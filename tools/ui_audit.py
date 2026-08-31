"""
손으로 만져야 드러나는 버그 — 화면 전수조사.

    python tools/ui_audit.py

★ 왜 이걸 따로 보나

  검사(pytest)는 서버가 무엇을 내놓는지 지킵니다. 화면 그래프는 화면과
  버튼이 이어져 있는지 봅니다. 그런데 **손가락으로 눌러야만 드러나는
  버그**는 둘 다 못 잡습니다. 코드는 멀쩡해 보이고 빌드도 통과합니다.

  실제로 이런 일이 있었습니다 — 정밀 시각 입력에서

      const bucket = HOURS.find(([, , h]) => h === s.hour);
      {bucket && <input value={s.hour} onChange={... s.set({hour}) ...} />}

  시를 고치는 순간 그 값이 어느 칸에도 안 맞아 `bucket` 이 undefined 가
  되고, **입력 칸이 통째로 사라집니다.** 한 글자도 못 고칩니다.

  그리고 분 칸은 `value={s.minute || ""}` 라 **0 을 적을 수가** 없었고,
  후기 칸은 `value` 도 `onChange` 도 없어 친 글자가 사라졌습니다.

★ 이 도구가 찾는 것

  1. 값만 있고 바꿀 길이 없는 칸      (value 는 있는데 onChange 가 없음)
  2. 0 을 못 넣는 칸                 (value={x || ""} — 0 이 빈칸이 됨)
  3. 스스로를 지우는 칸               (그 칸이 바꾸는 값으로 자기 표시를 정함)
  4. 아무 일도 안 하는 버튼           (onClick 이 비었거나 없음)
  5. 되돌릴 수 없는 자동 진행         (누르자마자 다음 화면 — 고칠 길 없음)
  6. 실패해도 안 풀리는 바쁨 상태      (깨지면 버튼이 영영 「~하는 중이오」)
  7. 나갈 길 없는 오류 화면           (오류만 있고 버튼이 하나도 없음)
  8. 이름표만 바뀌는 화면             (앞사람 상태가 그대로 넘어감)

  6·7·8 은 2026-09-01 에 실제로 셋 다 걸린 자리가 있어 붙였습니다 —
  리포트 화면이 한 번 깨지면 나갈 길이 없었고, 캐릭터를 옮겨도 앞사람에게
  적은 추가 입력이 그대로 실려 갔습니다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 태그 하나를 통째로 잡습니다 (여러 줄 걸침)
TAG = re.compile(r"<(input|textarea|select|button)\b((?:[^<>]|\{[^{}]*\})*?)/?>",
                 re.S)

# 실패해도 괜찮은 곁길 — 계측·공감률·배경 보충. 삼켜도 손님이 안 멈춥니다.
SIDE = ("track", "feedback", "agreement", "countShare", "getChart", "hook")


def files():
    for p in sorted(list((WEB / "app").rglob("*.tsx")) +
                    list((WEB / "components").rglob("*.tsx"))):
        if p.name == "DevRail.tsx":       # 관리자 레일은 개발 도구
            continue
        yield p


def strip_comments(src: str) -> str:
    """주석 속 예시 코드를 버그로 세면 안 됩니다. 줄 번호는 지킵니다."""
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                 src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def line_of(src: str, at: int) -> int:
    return src.count("\n", 0, at) + 1


def block_after(code: str, at: int, span: int = 900) -> str:
    return code[at:at + span]


def main() -> int:
    print("=" * 76)
    print("  화면 전수조사 — 눌러야 드러나는 버그")
    print("=" * 76)

    found = []

    def hit(rel, line, what, why):
        found.append((rel, line, what, why))

    for p in files():
        rel = str(p.relative_to(WEB))
        code = strip_comments(p.read_text(encoding="utf-8"))

        for m in TAG.finditer(code):
            tag, attrs = m.group(1), m.group(2)
            line = line_of(code, m.start())

            if tag in ("input", "textarea", "select"):
                # ── 1 · 값만 있고 바꿀 길이 없는 칸 ─────────
                has_value = re.search(r"\bvalue=|\bchecked=", attrs)
                has_change = re.search(r"\bonChange=|\breadOnly\b|\bdisabled\b",
                                       attrs)
                if has_value and not has_change:
                    hit(rel, line, "값만 있고 바꿀 길이 없는 %s" % tag,
                        "손님이 친 글자가 사라집니다")

                # ── 2 · 0 을 못 넣는 칸 ───────────────────
                z = re.search(r"value=\{[^}]*\|\|\s*\"\"\s*\}", attrs)
                if z:
                    hit(rel, line, "0 을 못 넣는 칸  %s" % z.group(0)[:44],
                        "0 · 빈 문자열이 falsy 라 지워집니다")

            # ── 4 · 아무 일도 안 하는 버튼 ─────────────────
            if tag == "button" and \
                    re.search(r"onClick=\{\s*\(\s*\)\s*=>\s*\{\s*\}\s*\}", attrs):
                hit(rel, line, "아무 일도 안 하는 버튼", "눌러도 반응이 없습니다")

        # ── 3 · 스스로를 지우는 칸 ──────────────────────────
        #
        #   어떤 값으로 **표시 여부**를 정해 놓고, 그 안의 칸이 같은 값을
        #   바꾸면 — 고치는 순간 칸이 사라집니다.
        #
        #   ★ 가드 **안에 진짜 입력 칸이 있을 때만** 셉니다. 안 그러면
        #     「날을 다 적어야 하오」 같은 안내 문구까지 버그로 셉니다
        #     (처음 판이 그래서 넷을 헛짚었습니다).
        for g in re.finditer(
                r"const\s+(\w+)\s*=\s*[^\n;]*?\b(s|session)\.(\w+)\b[^\n;]*?;",
                code):
            name, field = g.group(1), g.group(3)
            for gd in re.finditer(r"\{\s*[^}\n]{0,60}?\b%s\s*&&" % re.escape(name),
                                  code):
                inner = block_after(code, gd.start())
                if not re.search(r"<(input|textarea|select)\b", inner):
                    continue     # 안내 문구일 뿐이다
                if re.search(r"set\(\s*\{[^}]*\b%s\s*:" % re.escape(field), inner):
                    hit(rel, line_of(code, gd.start()),
                        "스스로를 지우는 칸  %s ← s.%s" % (name, field),
                        "그 칸을 고치면 %s 가 무너져 칸이 사라집니다" % name)

        # ── 5 · 되돌릴 수 없는 자동 진행 ────────────────────
        for m in re.finditer(
                r"onClick=\{\s*\(\)\s*=>\s*\{[^}]*?s\.set\([^)]*\)[^}]*?setStep\(",
                code, re.S):
            hit(rel, line_of(code, m.start()), "고르자마자 다음 화면",
                "잘못 골랐다는 걸 그때 알면 되돌아갈 길이 뒤로뿐")

        # ── 6 · 실패해도 안 풀리는 바쁨 상태 ────────────────
        for m in re.finditer(
                r"const \[(\w+), (set\w+)\] = useState\(\s*false", code):
            name, setter = m.group(1), m.group(2)
            if not re.search(r"%s\(true\)" % setter, code):
                continue
            # 비동기와 엮인 것만 봅니다 — 순수 토글은 실패할 일이 없습니다
            if not re.search(r"%s\(true\)[^;]{0,200}?(await|api\.|\.then)" % setter,
                             code, re.S) and \
               not re.search(r"(await|api\.|\.then)[^;]{0,400}?%s\(false\)" % setter,
                             code, re.S):
                continue
            resets = re.findall(r"(?:\.catch\(|catch\s*[({]|finally\s*\{)"
                                r"(?:[^;]|;){0,400}?%s\(false\)" % setter, code)
            if not resets:
                hit(rel, line_of(code, m.start()),
                    "실패해도 안 풀리는 바쁨 상태  %s" % name,
                    "깨지면 버튼이 영영 「~하는 중이오」 로 멈춥니다")

        # ── 7 · 나갈 길 없는 오류 화면 ──────────────────────
        for m in re.finditer(
                r"if\s*\(\s*(?:err|error)\s*\)\s*\{\s*return\s*\(?(.{0,900}?)\n\s*\}",
                code, re.S):
            blk = m.group(1)
            if "<button" not in blk and "router.push" not in blk and \
                    "<Link" not in blk:
                hit(rel, line_of(code, m.start()), "나갈 길 없는 오류 화면",
                    "한 번 깨지면 뒤로 버튼 말고는 나갈 데가 없습니다")

        # ── 8 · 이름표만 바뀌는 화면 ────────────────────────
        #
        #   `/report/[id]` 는 캐릭터가 바뀌어도 **같은 화면**입니다.
        #   리액트는 같은 자리로 보고 상태를 물려줍니다.
        if p.name == "page.tsx" and "[" in rel:
            n = len(re.findall(r"useState", code))
            keeps = re.search(r"useState\(\s*(?:params\.\w+|\w*[Ii]d)\s*\)", code)
            if n > 2 and not keeps:
                hit(rel, 1, "이름표만 바뀌는데 상태를 안 지움 (useState %d개)" % n,
                    "앞 사람에게 적은 것이 다음 사람에게 그대로 실려 갑니다")

    if not found:
        print("\n  [OK] 걸리는 자리 없음")
        return 0

    print()
    by: dict[str, list] = {}
    for rel, line, what, why in found:
        by.setdefault(what.split("  ")[0], []).append((rel, line, what, why))

    for kind, rows in sorted(by.items(), key=lambda kv: -len(kv[1])):
        print("  ★ %s — %d곳" % (kind, len(rows)))
        for rel, line, what, why in rows:
            print("     %-34s %4d  %s" % (rel[:34], line, why))
        print()

    print("-" * 76)
    print("  걸린 자리 %d곳" % len(found))
    print("  ※ 정적으로 보는 것이라 오탐이 섞입니다. 하나씩 눈으로 보고")
    print("    실제로 눌러 확인해야 합니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
