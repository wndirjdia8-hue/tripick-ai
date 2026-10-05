import streamlit as st
from PIL import Image
from pathlib import Path
import tempfile, subprocess, shutil, html, asyncio

st.set_page_config(page_title='TRIPICK AI', page_icon='✈️', layout='wide')
st.title('✈️ TRIPICK AI')
st.caption('사진 → 움직이는 세로 여행영상 → 한국어 여성 나레이션 → 제휴 게시글 · v2.2')

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
    st.info('Artlist 크레딧 없이 한국어 여성 TTS를 사용합니다. 목소리 느낌을 선택하고 미리 들을 수 있어요.')

files = st.file_uploader('숙소 사진을 순서대로 올려주세요 (최대 14장)', type=['jpg','jpeg','png','webp'], accept_multiple_files=True)
script = st.text_area('🎙️ 나레이션 문구', value=DEFAULT_SCRIPT, height=150)

st.subheader('📝 게시글')
caption = f'''{AFFILIATES[affiliate]}\n\n탁 트인 풍경부터 수영장과 스파까지 🌿\n여유롭게 쉬어가기 좋은 숙소예요.\n\n📌 다음 여행을 위해 저장해두세요.\n💌 숙소 정보가 궁금하다면 DM으로 ‘숙소’라고 보내주세요.\n\n#숙소추천 #여행추천 #감성숙소 #국내여행 #트리픽'''
st.text_area('복사해서 게시하세요', value=caption, height=220)

VOICE_PRESETS = {
    '일상적인': {'rate': '+8%', 'pitch': '+0Hz', 'preview_rate': 1.08, 'preview_pitch': 1.02},
    '부드러운': {'rate': '-3%', 'pitch': '-2Hz', 'preview_rate': 0.96, 'preview_pitch': 0.98},
    '밝은': {'rate': '+10%', 'pitch': '+4Hz', 'preview_rate': 1.10, 'preview_pitch': 1.08},
    '차분한': {'rate': '-8%', 'pitch': '-4Hz', 'preview_rate': 0.92, 'preview_pitch': 0.95},
    '활기찬': {'rate': '+15%', 'pitch': '+6Hz', 'preview_rate': 1.15, 'preview_pitch': 1.10},
}

def resolved_voice_style():
    if voice_style != '자동 추천':
        return voice_style
    # v2.2의 자동 추천은 채널/길이에 맞춘 안전한 기본 추천입니다.
    if channel in ['틱톡', '유튜브 쇼츠'] or duration == 15:
        return '밝은'
    if duration == 30:
        return '차분한'
    return '일상적인'

selected_voice = resolved_voice_style()
vp = VOICE_PRESETS[selected_voice]
st.caption(f'🎧 적용 목소리: {selected_voice}' + (' (자동 추천)' if voice_style == '자동 추천' else ''))
spoken = html.escape(script).replace('`','')
voice_html = f'''<div style="display:flex;gap:8px;align-items:center;margin:4px 0 16px 0"><button onclick="tripickSpeak()" style="padding:10px 16px;border:0;border-radius:8px;background:#111827;color:white;cursor:pointer">▶ {selected_voice} 미리듣기</button><button onclick="window.speechSynthesis.cancel()" style="padding:10px 16px;border:1px solid #bbb;border-radius:8px;background:white;cursor:pointer">■ 정지</button></div><script>function tripickSpeak(){{window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(`{spoken}`);u.lang='ko-KR';u.rate={vp['preview_rate']};u.pitch={vp['preview_pitch']};const voices=window.speechSynthesis.getVoices();const ko=voices.filter(v=>(v.lang||'').toLowerCase().startsWith('ko'));u.voice=ko.find(v=>['female','sunhi','yuna','heami','sora','seoyeon'].some(h=>v.name.toLowerCase().includes(h)))||ko[0]||null;window.speechSynthesis.speak(u);}}</script>'''
st.components.v1.html(voice_html, height=60)

async def make_tts(text, out_path, style):
    import edge_tts
    preset = VOICE_PRESETS[style]
    communicate = edge_tts.Communicate(text, 'ko-KR-SunHiNeural', rate=preset['rate'], pitch=preset['pitch'])
    await communicate.save(str(out_path))

def run(cmd, timeout=180):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)

if files:
    files = files[:14]
    st.subheader(f'📷 사진 {len(files)}장')
    cols = st.columns(5)
    for i, f in enumerate(files):
        with cols[i % 5]: st.image(f, caption=f'{i+1}. {f.name}', use_container_width=True)
    st.caption('권장 순서: 전경 → 외관 → 야외 → 거실/주방 → 침실 → 욕실 → 수영장/스파 → 마무리')

    if st.button('🎬 음성 포함 영상 만들기', type='primary', use_container_width=True):
        work = Path(tempfile.mkdtemp(prefix='tripick_'))
        try:
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
                    asyncio.run(make_tts(script, voice, selected_voice))
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
            st.success('완성! 움직이는 여행영상' + (f' + {selected_voice} 여성 나레이션' if voice_ok else ' (무음)'))
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
