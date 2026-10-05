
import streamlit as st
from PIL import Image
import tempfile, subprocess, os, math, shutil
from pathlib import Path

st.set_page_config(page_title="TRIPICK AI", page_icon="✈️", layout="wide")

st.title("✈️ TRIPICK AI")
st.caption("숙소 사진 → 9:16 여행 쇼츠 자동 제작 · v1")

with st.sidebar:
    st.header("영상 설정")
    duration = st.selectbox("영상 길이", [15, 20, 30], index=1)
    fps = st.selectbox("프레임", [24, 30], index=0)
    st.write("출력: 1080 × 1920 · MP4")
    st.info("v1은 사진에 부드러운 줌/팬 효과를 적용해 저비용으로 영상을 만듭니다.")

files = st.file_uploader(
    "숙소 사진을 순서대로 올려주세요 (최대 14장)",
    type=["jpg","jpeg","png","webp"],
    accept_multiple_files=True
)

if files:
    files = files[:14]
    st.subheader(f"사진 {len(files)}장")
    cols = st.columns(5)
    for i, f in enumerate(files):
        with cols[i % 5]:
            st.image(f, caption=f"{i+1}. {f.name}", use_container_width=True)

    st.markdown("**추천 순서:** 전경 → 외관 → 야외 → 수영장 → 거실 → 주방 → 침실 → 욕실 → 스파 → 엔딩")

    if st.button("🎬 여행쇼츠 만들기", type="primary", use_container_width=True):
        work = Path(tempfile.mkdtemp(prefix="tripick_"))
        try:
            n = len(files)
            if n == 0:
                st.error("사진을 먼저 올려주세요.")
                st.stop()

            per = duration / n
            segments = []

            progress = st.progress(0, text="사진을 영상으로 변환하는 중...")

            for i, f in enumerate(files):
                src = work / f"src_{i:02d}.jpg"
                img = Image.open(f).convert("RGB")
                img.save(src, quality=95)

                seg = work / f"seg_{i:02d}.mp4"
                frames = max(1, int(per * fps))

                # 세로 쇼츠: 중앙 크롭 + 아주 부드러운 줌인.
                vf = (
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    f"zoompan=z='min(zoom+0.0008,1.08)':"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                    f"d={frames}:s=1080x1920:fps={fps},"
                    "format=yuv420p"
                )

                cmd = [
                    "ffmpeg","-y","-loop","1","-i",str(src),
                    "-vf",vf,"-t",f"{per:.3f}",
                    "-an","-c:v","libx264","-preset","veryfast","-crf","20",
                    "-pix_fmt","yuv420p",str(seg)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                segments.append(seg)
                progress.progress((i+1)/n * 0.8, text=f"{i+1}/{n} 장 처리 완료")

            concat = work / "concat.txt"
            concat.write_text("\n".join([f"file '{p.as_posix()}'" for p in segments]), encoding="utf-8")

            final = work / "TRIPICK_travel_short.mp4"
            cmd = [
                "ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),
                "-c:v","libx264","-preset","veryfast","-crf","20",
                "-pix_fmt","yuv420p","-movflags","+faststart",
                "-t",str(duration),str(final)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            progress.progress(1.0, text="완성!")

            data = final.read_bytes()
            st.success("여행쇼츠가 완성됐어요.")
            st.video(data)
            st.download_button(
                "⬇️ MP4 저장",
                data=data,
                file_name="TRIPICK_travel_short.mp4",
                mime="video/mp4",
                use_container_width=True
            )
        except subprocess.CalledProcessError:
            st.error("영상 생성 중 오류가 발생했어요. FFmpeg 설치 여부를 확인해주세요.")
        finally:
            shutil.rmtree(work, ignore_errors=True)
else:
    st.info("먼저 숙소 사진을 올려주세요.")

st.divider()
st.caption("다음 버전 예정: AI 사진 자동분류 · 감성 나레이션 · 여성 음성 · BGM · 인스타 게시글 · DM 답변 자동 생성")
