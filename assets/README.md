# assets — 에셋 원본 보관소

`public/` 에 들어가는 파일은 **전부 여기서 뽑은 인코딩본**입니다.
원본을 잃으면 화질을 못 올리고, 규격이 바뀌어도 다시 못 뽑습니다.

```
assets/master/scene/{id}/{계절}.mp4      장면 원본   ← .gitignore 대상
assets/master/char/{id}.png              인물 원본   ← .gitignore 대상
        ↓ 인코딩
apps/web/public/scene/{id}/clip.mp4      H.264 · 600KB 이하
apps/web/public/scene/{id}/clip.webm     VP9   · 600KB 이하
apps/web/public/scene/{id}/poster.jpg    첫 프레임
```

**원본은 커밋하지 않습니다.** 20MB 짜리가 스무 개면 리포가 죽습니다.
구글 드라이브 폴더 자체가 동기화되므로 백업은 그쪽에 맡깁니다.

규격은 `docs/10_에셋제작_발주서.md` §7 이 원본입니다.

---

## 지금 들어있는 것

| 원본 | 규격 |
|---|---|
| `master/scene/gate/summer.mp4` | 1920×1080 · HEVC · 5.06s · 19.1MB |

여기서 뽑아 `apps/web/public/scene/gate/` 에 넣었습니다.

```
clip.mp4    1280×720 · H.264 crf30 · 무음 · faststart   462KB
clip.webm   1280×720 · VP9  crf40 · 무음                462KB
poster.jpg  1280×720 · 첫 프레임                        133KB
```

**계절 폴더는 두지 않았습니다.** `gate` 는 기본 한 장으로 사계절이
굴러갑니다(발주서 §8). 여름판을 `gate/summer/` 에도 복제해 두면
바이트가 똑같은 파일이 리포에 두 벌 박히는데, git 은 지워도 히스토리에
남습니다. 봄·가을·겨울판을 **실제로 다르게** 뽑았을 때 그 계절 폴더에만
넣으세요. 그때부터 그 계절만 갈아탑니다.

### 다시 뽑을 때

```bash
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
SRC=assets/master/scene/gate/summer.mp4
OUT=apps/web/public/scene/gate

"$FF" -i "$SRC" -an -c:v libx264 -crf 30 -preset slow -vf scale=1280:-2 -pix_fmt yuv420p -movflags +faststart "$OUT/clip.mp4"
"$FF" -i "$SRC" -an -c:v libvpx-vp9 -crf 40 -b:v 0 -row-mt 1 -vf scale=1280:-2 -pix_fmt yuv420p "$OUT/clip.webm"
"$FF" -i "$SRC" -vf scale=1280:-2 -frames:v 1 -q:v 4 "$OUT/poster.jpg"
```

ffmpeg 를 따로 깔 필요 없습니다. `imageio-ffmpeg` 가 바이너리를 물고 있습니다.

`crf` 를 올리면 작아집니다. 600KB 를 넘기지 마세요 — 대문은 첫 화면이라
이 숫자가 그대로 첫인상 로딩 시간입니다.

### poster.jpg 는 반드시 있어야 합니다

`Scene.tsx` 의 `useClipBase` 가 **`poster.jpg` 를 HEAD 로 찔러 보고**
에셋 유무를 판정합니다. 이게 없으면 clip 이 멀쩡히 있어도 자리표시
SVG 가 뜹니다.
