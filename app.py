import streamlit as st
from PIL import Image
from pathlib import Path
import tempfile, subprocess, shutil, requests

st.set_page_config(page_title='TRIPICK AI', page_icon='✈️', layout='wide')
st.title('✈️ TRIPICK AI')
st.caption('사진 → 움직이는 세로 여행영상 → ElevenLabs 한국어 나레이션 → 제휴 게시글 · v2.4')

AFFILIATES = {
    '쿠팡 파트너스': '[광고] 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.',
    '세시간전': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    '마이리얼트립': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    '아고다': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    'Trip.com': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    '클룩(Klook)': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    'KKday': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    'Booking.com': '[광고] 제휴 링크를 통해 예약이 발생하면 일정액의 수수료를 제공받을 수 있습니다.',
    '기타': '[광고] 이 게시물에는 제휴 링크가 포함되어 있으며, 구매·예약 시 일정액의 수수료를 제공받을 수 있습니다.'
}
DEFAULT_SCRIPT = '''눈앞에 펼쳐지는 탁 트인 풍경, 이런 곳에서 하루를 보내면 어떨까요?\n여유로운 야외 공간에 깔끔한 거실과 편안한 침실, 수영장과 스파까지.\n다음 여행을 위해 꼭 저장해두세요.\n숙소가 궁금하다면 DM으로 ‘숙소’라고 보내주세요.'''

with st.sidebar:
    st.header('제작 설정')
    duration = st.selectbox('영상 길이', [15, 20, 30], index=1)
    affiliate = st.selectbox('제휴처', list(AFFILIATES.keys()))
    channel = st.selectbox('게시 채널', ['인스타 릴스', '틱톡', '유튜브 쇼츠', '네이버 블로그'])
    motion = st.selectbox('영상 움직임', ['부드러운 줌 + 좌우 패닝', '줌 중심'], index=0)
    voice_style = st.selectbox('나레이션 목소리', ['자동 추천', '일상적인', '부드러운', '밝은', '차분한', '활기찬'], index=0)
    st.caption('출력: 720×1280 MP4 (세로 9:16)')
    st.info('ElevenLabs 실제 목소리를 선택해 한국어 나레이션을 만들어요. Artlist 크레딧은 사용하지 않습니다.')

files = st.file_uploader('숙소 사진을 순서대로 올려주세요 (최대 14장)', type=['jpg','jpeg','png','webp'], accept_multiple_files=True)
script = st.text_area('🎙️ 나레이션 문구', value=DEFAULT_SCRIPT, height=150)

st.subheader('📝 게시글')
caption = f'''{AFFILIATES[affiliate]}\n\n탁 트인 풍경부터 수영장과 스파까지 🌿\n여유롭게 쉬어가기 좋은 숙소예요.\n\n📌 다음 여행을 위해 저장해두세요.\n💌 숙소 정보가 궁금하다면 DM으로 ‘숙소’라고 보내주세요.\n\n#숙소추천 #여행추천 #감성숙소 #국내여행 #트리픽'''
st.text_area('복사해서 게시하세요', value=caption, height=220)

ELEVEN_API = "https://api.elevenlabs.io/v1"

def eleven_key():
    try:
        return st.secrets["ELEVENLABS_API_KEY"]
    except Exception:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def load_eleven_voices(api_key):
    r = requests.get(f"{ELEVEN_API}/voices", headers={"xi-api-key": api_key}, timeout=20)
    r.raise_for_status()
    voices = r.json().get("voices", [])
    # Prefer voices explicitly labelled female. If labels are sparse, keep all so the user can still choose.
    female = [v for v in voices if str((v.get("labels") or {}).get("gender", "")).lower() == "female"]
    pool = female or voices
    return sorted(pool, key=lambda v: (v.get("name") or "").lower())

api_key = eleven_key()
voices = []
selected_voice = None
if api_key:
    try:
        voices = load_eleven_voices(api_key)
    except Exception as e:
        st.warning(f"ElevenLabs 목소리 목록을 불러오지 못했어요: {type(e).__name__}")

if voices:
    names = []
    by_name = {}
    for v in voices:
        labels = v.get("labels") or {}
        desc = labels.get("description") or labels.get("use_case") or labels.get("age") or ""
        label = f"{v.get('name','Voice')}" + (f" · {desc}" if desc else "")
        # Keep labels unique even when voice names collide.
        if label in by_name:
            label += f" · {v.get('voice_id','')[:6]}"
        names.append(label); by_name[label] = v
    voice_choice = st.sidebar.selectbox("ElevenLabs 실제 목소리", names, index=0)
    selected_voice = by_name[voice_choice]
    st.caption(f"🎧 ElevenLabs 선택 목소리: {selected_voice.get('name','Voice')}")
else:
    st.sidebar.caption("ElevenLabs 목소리 목록을 불러오면 실제 성우 선택칸이 나타납니다.")
    if not api_key:
        st.warning("Streamlit 비밀에 ELEVENLABS_API_KEY가 없습니다. 앱 설정 → 비밀에서 키를 저장해 주세요.")

VOICE_SETTINGS = {
    '일상적인': {'stability': 0.45, 'similarity_boost': 0.78, 'style': 0.15},
    '부드러운': {'stability': 0.58, 'similarity_boost': 0.78, 'style': 0.10},
    '밝은': {'stability': 0.38, 'similarity_boost': 0.76, 'style': 0.32},
    '차분한': {'stability': 0.68, 'similarity_boost': 0.80, 'style': 0.08},
    '활기찬': {'stability': 0.32, 'similarity_boost': 0.75, 'style': 0.42},
}

def resolved_voice_style():
    if voice_style != '자동 추천': return voice_style
    if channel in ['틱톡', '유튜브 쇼츠'] or duration == 15: return '밝은'
    if duration == 30: return '차분한'
    return '일상적인'

selected_voice_style = resolved_voice_style()
st.caption(f"🎚️ 말투 설정: {selected_voice_style}" + (' (자동 추천)' if voice_style == '자동 추천' else ''))

PREVIEW_TEXT = "탁 트인 풍경과 여유로운 공간, 다음 여행은 여기 어떠세요?"

def make_tts(text, out_path, voice_id, style, api_key):
    settings = VOICE_SETTINGS[style]
    url = f"{ELEVEN_API}/text-to-speech/{voice_id}"
    params = {"output_format": "mp3_44100_128"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": settings['stability'],
            "similarity_boost": settings['similarity_boost'],
            "style": settings['style'],
            "use_speaker_boost": True,
        },
    }
    r = requests.post(url, params=params, headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}, json=payload, timeout=90)
    if r.status_code >= 400:
        try: detail = r.json().get("detail", r.text)
        except Exception: detail = r.text
        raise RuntimeError(f"ElevenLabs {r.status_code}: {str(detail)[:500]}")
    out_path.write_bytes(r.content)

if selected_voice and api_key:
    st.caption("🇰🇷 모든 성우는 같은 짧은 한국어 문장으로 비교합니다. 미리듣기 생성 시 ElevenLabs 크레딧이 소량 사용됩니다.")
    if st.button("▶ 선택 성우 한국어 미리듣기", use_container_width=False):
        preview_dir = Path(tempfile.mkdtemp(prefix='tripick_preview_'))
        try:
            preview_path = preview_dir / 'preview.mp3'
            with st.spinner('선택한 성우의 한국어 미리듣기를 만드는 중이에요…'):
                make_tts(PREVIEW_TEXT, preview_path, selected_voice['voice_id'], selected_voice_style, api_key)
            st.audio(preview_path.read_bytes(), format='audio/mpeg')
            st.caption(f"미리듣기 문장: {PREVIEW_TEXT}")
        except Exception as e:
            st.error(f"한국어 미리듣기 생성 실패: {type(e).__name__}: {e}")
        finally:
            shutil.rmtree(preview_dir, ignore_errors=True)

def run(cmd, timeout=180):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)

if files:
    files = files[:14]
    st.subheader(f'📷 사진 {len(files)}장')
    cols = st.columns(5)
    for i, f in enumerate(files):
        with cols[i % 5]: st.image(f, caption=f'{i+1}. {f.name}', use_container_width=True)
    st.caption('권장 순서: 전경 → 외관 → 야외 → 거실/주방 → 침실 → 욕실 → 수영장/스파 → 마무리')

    if st.button('🎬 ElevenLabs 음성 포함 영상 만들기', type='primary', use_container_width=True):
        work = Path(tempfile.mkdtemp(prefix='tripick_'))
        try:
            if not api_key or not selected_voice:
                st.error('ElevenLabs 연결 또는 목소리 선택을 먼저 확인해 주세요.')
                st.stop()
            W,H,FPS = 720,1280,24
            n=len(files); trans=0.35
            clip = duration/n + trans
            frames=max(2, round(clip*FPS))
            image_paths=[]
            for i,f in enumerate(files):
                p=work/f'img_{i:02d}.jpg'
                Image.open(f).convert('RGB').save(p, quality=90, optimize=True)
                image_paths.append(p)

            # One FFmpeg render with Ken Burns motion and crossfades.
            cmd=['ffmpeg','-y']
            for p in image_paths:
                cmd += ['-loop','1','-t',f'{clip:.3f}','-i',str(p)]
            filters=[]
            for i in range(n):
                # Overscale first so pan/zoom never reveals empty edges.
                base=f'[{i}:v]scale=900:1600:force_original_aspect_ratio=increase,crop=900:1600'
                if motion == '줌 중심':
                    zp=f"zoompan=z='min(zoom+0.0009,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
                elif i % 3 == 0:
                    zp=f"zoompan=z='min(zoom+0.0008,1.09)':x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
                elif i % 3 == 1:
                    zp=f"zoompan=z='min(zoom+0.0008,1.09)':x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
                else:
                    zp=f"zoompan=z='min(zoom+0.0009,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
                filters.append(f"{base},{zp},format=yuv420p[v{i}]")
            if n == 1:
                outlabel='v0'
            else:
                prev='v0'
                for i in range(1,n):
                    out=f'x{i}'
                    offset=i*(clip-trans)
                    filters.append(f'[{prev}][v{i}]xfade=transition=fade:duration={trans}:offset={offset:.3f}[{out}]')
                    prev=out
                outlabel=prev
            silent=work/'silent.mp4'
            cmd += ['-filter_complex',';'.join(filters),'-map',f'[{outlabel}]','-t',str(duration),'-an','-c:v','libx264','-preset','ultrafast','-crf','25','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
            with st.spinner('사진에 움직임과 전환을 넣는 중이에요…'):
                cp=run(cmd, 180)
            if cp.returncode != 0:
                st.error('영상 생성에 실패했어요. 아래 오류를 보내주세요.')
                st.code(cp.stderr[-3500:])
                st.stop()

            final=work/'TRIPICK_travel_short_voice.mp4'
            voice=work/'voice.mp3'
            voice_ok=False
            try:
                with st.spinner('한국어 여성 나레이션을 만드는 중이에요…'):
                    make_tts(script, voice, selected_voice['voice_id'], selected_voice_style, api_key)
                # Fit narration to the selected video duration only if it is too long.
                probe=run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(voice)],30)
                vd=float(probe.stdout.strip() or '0')
                if vd > duration and vd > 0:
                    speed=vd/duration
                    # atempo supports 0.5..2.0; our narration is expected to stay in this range.
                    af=f'atempo={min(speed,2.0):.4f}'
                else:
                    af='anull'
                mix=run(['ffmpeg','-y','-i',str(silent),'-i',str(voice),'-filter:a',af,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(duration),'-shortest','-movflags','+faststart',str(final)],90)
                voice_ok = mix.returncode == 0 and final.exists()
            except Exception as e:
                st.warning(f'음성 생성은 건너뛰었어요: {type(e).__name__}. 영상은 정상 저장할 수 있어요.')

            chosen = final if voice_ok else silent
            data=chosen.read_bytes()
            st.success('완성! 움직이는 여행영상' + (f" + {selected_voice.get('name','ElevenLabs')} 나레이션" if voice_ok else ' (무음)'))
            st.video(data)
            st.download_button('⬇️ MP4 저장',data=data,file_name='TRIPICK_travel_short.mp4',mime='video/mp4',use_container_width=True)
            if not voice_ok:
                st.info('음성 서비스가 일시적으로 실패해도 영상 제작은 성공하도록 안전장치를 넣었습니다.')
        except subprocess.TimeoutExpired:
            st.error('영상 처리 시간이 초과됐어요. 사진은 그대로 두고 다시 한 번 시도해 주세요.')
        except Exception as e:
            st.error(f'오류: {type(e).__name__}: {e}')
        finally:
            shutil.rmtree(work,ignore_errors=True)
else:
    st.info('사진을 올리면 영상 제작 버튼이 나타납니다.')
