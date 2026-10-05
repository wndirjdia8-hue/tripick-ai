import streamlit as st
from PIL import Image
from pathlib import Path
import tempfile, subprocess, shutil, os, html, urllib.parse, urllib.request

st.set_page_config(page_title='TRIPICK AI', page_icon='✈️', layout='wide')
st.title('✈️ TRIPICK AI')
st.caption('사진 → 세로 여행영상 → 한국어 여성 나레이션 → 제휴 게시글 · v2')

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

DEFAULT_SCRIPT = '''눈앞에 펼쳐지는 탁 트인 풍경, 이런 곳에서 하루를 보내면 어떨까요?
여유로운 야외 공간에 깔끔한 거실과 편안한 침실, 수영장과 스파까지.
다음 여행을 위해 꼭 저장해두세요.
숙소가 궁금하다면 DM으로 ‘숙소’라고 보내주세요.'''

with st.sidebar:
    st.header('제작 설정')
    duration = st.selectbox('영상 길이', [15, 20, 30], index=1)
    affiliate = st.selectbox('제휴처', list(AFFILIATES.keys()))
    channel = st.selectbox('게시 채널', ['인스타 릴스', '틱톡', '유튜브 쇼츠', '네이버 블로그'])
    st.caption('영상: 1080×1920 · MP4')
    st.info('음성은 브라우저에서 생성해 서버 부담을 줄입니다. 별도 Artlist 크레딧을 사용하지 않습니다.')

files = st.file_uploader('숙소 사진을 순서대로 올려주세요 (최대 14장)', type=['jpg','jpeg','png','webp'], accept_multiple_files=True)

script = st.text_area('🎙️ 나레이션 문구', value=DEFAULT_SCRIPT, height=150)

st.subheader('📝 게시글')
caption = f'''{AFFILIATES[affiliate]}\n\n탁 트인 풍경부터 수영장과 스파까지 🌿\n여유롭게 쉬어가기 좋은 숙소예요.\n\n📌 다음 여행을 위해 저장해두세요.\n💌 숙소 정보가 궁금하다면 DM으로 ‘숙소’라고 보내주세요.\n\n#숙소추천 #여행추천 #감성숙소 #국내여행 #트리픽'''
st.text_area('복사해서 게시하세요', value=caption, height=220)

# Browser-native Korean TTS preview. This does not consume server CPU or paid credits.
spoken = html.escape(script).replace('`','')
voice_html = f'''
<div style="display:flex;gap:8px;align-items:center;margin:4px 0 16px 0">
<button onclick="tripickSpeak()" style="padding:10px 16px;border:0;border-radius:8px;background:#111827;color:white;cursor:pointer">▶ 여성 음성 미리듣기</button>
<button onclick="window.speechSynthesis.cancel()" style="padding:10px 16px;border:1px solid #bbb;border-radius:8px;background:white;cursor:pointer">■ 정지</button>
</div>
<script>
function tripickSpeak() {{
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(`{spoken}`);
  u.lang='ko-KR'; u.rate=1.08; u.pitch=1.02;
  const voices=window.speechSynthesis.getVoices();
  const ko=voices.filter(v => (v.lang||'').toLowerCase().startsWith('ko'));
  const femaleHints=['female','sunhi','yuna','heami','sora','ji','seoyeon'];
  u.voice=ko.find(v => femaleHints.some(h => v.name.toLowerCase().includes(h))) || ko[0] || null;
  window.speechSynthesis.speak(u);
}}
</script>'''
st.components.v1.html(voice_html, height=60)

if files:
    files = files[:14]
    st.subheader(f'📷 사진 {len(files)}장')
    cols = st.columns(5)
    for i, f in enumerate(files):
        with cols[i % 5]: st.image(f, caption=f'{i+1}. {f.name}', use_container_width=True)
    st.caption('권장 순서: 전경 → 외관 → 야외 → 거실/주방 → 침실 → 욕실 → 수영장/스파 → 마무리')

    if st.button('🎬 영상 만들기', type='primary', use_container_width=True):
        work = Path(tempfile.mkdtemp(prefix='tripick_'))
        try:
            # 720x1280 while rendering: far lighter on Community Cloud. Browser/platform upscales cleanly for social preview.
            W,H,FPS = 720,1280,24
            n=len(files); per=duration/n
            concat=work/'inputs.txt'; lines=[]
            for i,f in enumerate(files):
                p=work/f'img_{i:02d}.jpg'
                Image.open(f).convert('RGB').save(p, quality=90, optimize=True)
                lines += [f"file '{p.as_posix()}'", f'duration {per:.5f}']
            lines += [f"file '{(work/f'img_{n-1:02d}.jpg').as_posix()}'"]
            concat.write_text('\n'.join(lines),encoding='utf-8')
            final=work/'TRIPICK_travel_short.mp4'
            # Single ffmpeg process: no per-photo H264 segments, much lower RAM/CPU/startup risk.
            vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p"
            cmd=['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-vf',vf,'-t',str(duration),'-an','-c:v','libx264','-preset','ultrafast','-crf','25','-movflags','+faststart',str(final)]
            with st.spinner('영상을 만드는 중이에요…'):
                cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=150)
            if cp.returncode != 0:
                st.error('영상 생성에 실패했어요. 아래 오류를 복사해 보내주세요.')
                st.code(cp.stderr[-3000:])
            else:
                data=final.read_bytes(); st.success('영상 완성!')
                st.video(data)
                st.download_button('⬇️ MP4 저장',data=data,file_name='TRIPICK_travel_short.mp4',mime='video/mp4',use_container_width=True)
                st.info('위 “여성 음성 미리듣기”로 나레이션을 확인할 수 있어요. v2.1에서는 선택한 음성을 MP4에 직접 합치는 기능을 붙일 수 있습니다.')
        except subprocess.TimeoutExpired:
            st.error('서버 영상 처리 시간이 초과됐어요. 사진 수를 줄이지 않아도 되도록 다음 배포에서 렌더러를 분리해야 합니다.')
        except Exception as e:
            st.error(f'오류: {type(e).__name__}: {e}')
        finally:
            shutil.rmtree(work,ignore_errors=True)
else:
    st.info('사진을 올리면 영상 제작 버튼이 나타납니다.')
