import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os
import re
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import json

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="AI Video Dubbing", page_icon="🎬")
st.title("🎬 AI Video Dubbing - ဇတ်ကားအသံပြောင်း")
st.markdown("**ဇတ်ကားထဲက ဇာတ်ဆောင်အသံတွေကို မြန်မာအသံနဲ့ အစားထိုးမယ်**")

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def extract_audio_segments(video_path, timestamps):
    """Video ကနေ အသံအပိုင်းလေးတွေထုတ်ယူ"""
    try:
        video = VideoFileClip(video_path)
        audio_segments = []
        
        for i, (start, end, text) in enumerate(timestamps):
            # အသံအပိုင်းလေးထုတ်
            segment_audio = video.audio.subclip(start, end)
            segment_path = f"temp_segment_{i}.wav"
            segment_audio.write_audiofile(segment_path, verbose=False, logger=None)
            audio_segments.append(segment_path)
        
        video.close()
        return audio_segments
    except Exception as e:
        st.error(f"Audio segment ထုတ်ယူရာတွင် error: {str(e)}")
        return None

def create_dubbed_video(original_video_path, burmese_audio_path, output_path="dubbed_video.mp4"):
    """မြန်မာအသံနဲ့ video ပြန်လုပ်ခြင်း"""
    try:
        # Original video ကိုဖွင့်
        video = VideoFileClip(original_video_path)
        
        # မြန်မာအသံကိုဖွင့်
        burmese_audio = AudioFileClip(burmese_audio_path)
        
        # Original audio ကို mute လုပ်ပြီး မြန်မာအသံထည့်
        video = video.without_audio()
        final_video = video.set_audio(burmese_audio)
        
        # Video သိမ်းခြင်း
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        video.close()
        burmese_audio.close()
        final_video.close()
        
        return output_path
    except Exception as e:
        st.error(f"Dubbed video ဖန်တီးရာတွင် error: {str(e)}")
        return None

uploaded_file = st.file_uploader("ဇတ်ကား/ဗီဒီယို ဖိုင်တင်ပေးပါ", 
                                type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🎭 အသံပြောင်းမယ် (Dubbing)"):
        with st.spinner('ဇတ်ကားထဲက အသံတွေကို မြန်မာလို ပြောင်းနေပါတယ်...'):
            try:
                # ၁။ Temporary file သိမ်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name
                
                st.info("🔍 ဇတ်ကားထဲက စကားသံတွေကို ဖော်ထုတ်နေပါတယ်...")
                
                # ၂။ Whisper နဲ့ transcription with timestamps
                result = model.transcribe(
                    video_path,
                    language=None,
                    task="transcribe",
                    verbose=False,
                    word_timestamps=True
                )
                
                # ၃။ Dialogue segments များရယူ
                dialogues = []
                current_segment = ""
                current_start = 0
                
                for segment in result['segments']:
                    text = segment['text'].strip()
                    start = segment['start']
                    end = segment['end']
                    
                    if text:  # စကားပြောတဲ့အပိုင်းပဲ
                        dialogues.append({
                            'text': text,
                            'start': start,
                            'end': end,
                            'duration': end - start
                        })
                
                st.success(f"✅ စကားပြောအပိုင်း {len(dialogues)} ပိုင်းတွေ့ရှိပြီ")
                
                # ၄။ မြန်မာလို ဘာသာပြန်ခြင်း
                st.info("🌐 မြန်မာလို ဘာသာပြန်နေပါတယ်...")
                
                # Dialogue တွေကို group လုပ်ခြင်း (context အတွက်)
                dialogue_texts = [d['text'] for d in dialogues]
                combined_text = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(dialogue_texts)])
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": """မင်းက professional video dubbing translator ဖြစ်တယ်။ 
                        ဇတ်ကားထဲက ဇာတ်ဆောင်တွေပြောတဲ့ စကားတွေကို မြန်မာလို dubbing လုပ်ဖို့ ပြန်ပေးရမယ်။
                        
                        **Dubbing အတွက် သတိထားရမယ့်အချက်များ:**
                        1. **Lip sync ကိုက်ညီအောင်** - ပါးစပ်လှုပ်ရှားမှုနဲ့ လိုက်ဖက်အောင်
                        2. **စကားပြောသံသဘာဝ** - ရုပ်ရှင်ထဲမှာ ပြောသလိုပြန်ရမယ်
                        3. **အာမေးမှုနဲ့လိုက်ဖက်** - စိတ်ခံစားမှုပေါ်မူတည်ပြီး ပြန်ရမယ်
                        4. **တိုတောင်းပြီးထိရောက်အောင်** - အသံထွက်ချိန်နဲ့ ကိုက်ညီအောင်
                        
                        **ပုံစံ:**
                        နံပါတ်တစ် စကား: [မူရင်း အင်္ဂလိပ်စာ]
                        မြန်မာပြန်: [မြန်မာလို dubbing version]
                        
                        ဘာသာပြန်ချက်တွေကို နံပါတ်တစ်ခုချင်းစီအတိုင်း ပြန်ပေးပါ။"""},
                        
                        {"role": "user", "content": f"""ဇတ်ကားထဲက ဇာတ်ဆောင်တွေပြောတဲ့ စကားတွေကို မြန်မာလို dubbing အတွက် ပြန်ပေးပါ။
                        တစ်ကြောင်းချင်းစီကို သီးသန့်ပြန်ပေးပါ။
                        
                        ဇတ်ကားစကားများ:
                        {combined_text}
                        
                        မြန်မာလို dubbing version:"""}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                
                translated_text = completion.choices[0].message.content
                
                # ၅။ Translated text ကို ခွဲခြားခြင်း
                burmese_dialogues = []
                lines = translated_text.strip().split('\n')
                
                for line in lines:
                    if ':' in line and ']' in line:
                        # Format: [1] မြန်မာပြန်
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            burmese_dialogues.append(parts[1].strip())
                
                # ၆။ မြန်မာအသံထုတ်ခြင်း (TTS)
                st.info("🗣️ မြန်မာအသံထုတ်နေပါတယ်...")
                
                # Dialogue တစ်ခုချင်းစီအတွက် audio ထုတ်
                burmese_audio_segments = []
                
                for i, (dialogue, burmese_text) in enumerate(zip(dialogues, burmese_dialogues)):
                    if i < len(burmese_dialogues):
                        try:
                            # TTS for each dialogue
                            output_segment = f"burmese_segment_{i}.mp3"
                            
                            # Adjust speech rate based on original duration
                            original_duration = dialogue['duration']
                            expected_words = len(burmese_text.split())
                            
                            # Calculate speech rate
                            if original_duration > 0:
                                words_per_second = expected_words / original_duration
                                rate_adjustment = "+0%"
                                if words_per_second > 3:
                                    rate_adjustment = "+15%"
                                elif words_per_second < 2:
                                    rate_adjustment = "-10%"
                            else:
                                rate_adjustment = "+0%"
                            
                            communicate = edge_tts.Communicate(
                                text=burmese_text,
                                voice="my-MM-ThihaNeural",
                                rate=rate_adjustment,
                                pitch="+0Hz"
                            )
                            
                            asyncio.run(communicate.save(output_segment))
                            burmese_audio_segments.append(output_segment)
                            
                        except Exception as e:
                            st.warning(f"Segment {i+1} အသံထုတ်ရာတွင် အခက်အခဲရှိ: {str(e)}")
                
                # ၇။ Audio segments များကို ပေါင်းစပ်ခြင်း
                if burmese_audio_segments:
                    st.info("🔊 အသံအပိုင်းတွေကို ပေါင်းစပ်နေပါတယ်...")
                    
                    # Create combined audio with original timing
                    final_audio = AudioSegment.silent(duration=int(dialogues[-1]['end'] * 1000))
                    
                    for i, (dialogue, audio_segment) in enumerate(zip(dialogues, burmese_audio_segments)):
                        if os.path.exists(audio_segment):
                            segment_audio = AudioSegment.from_mp3(audio_segment)
                            
                            # Adjust to fit original timing if needed
                            target_duration = int(dialogue['duration'] * 1000)
                            current_duration = len(segment_audio)
                            
                            if current_duration > target_duration:
                                # Speed up slightly
                                segment_audio = segment_audio.speedup(playback_speed=current_duration/target_duration)
                            elif current_duration < target_duration:
                                # Add silence at the end
                                silence_needed = target_duration - current_duration
                                silence = AudioSegment.silent(duration=silence_needed)
                                segment_audio = segment_audio + silence
                            
                            # Overlay at correct timing
                            start_ms = int(dialogue['start'] * 1000)
                            final_audio = final_audio.overlay(segment_audio, position=start_ms)
                    
                    # Save final dubbed audio
                    final_audio_path = "final_burmese_audio.wav"
                    final_audio.export(final_audio_path, format="wav")
                    
                    # ၈။ Dubbed video ဖန်တီးခြင်း
                    st.info("🎬 Dubbed video ဖန်တီးနေပါတယ်...")
                    
                    dubbed_video_path = create_dubbed_video(video_path, final_audio_path)
                    
                    if dubbed_video_path and os.path.exists(dubbed_video_path):
                        st.success("✅ Dubbing ပြီးပါပြီ!")
                        
                        # Show results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🎭 မူရင်းစကားများ")
                            for i, dialogue in enumerate(dialogues[:5]):  # Show first 5
                                st.write(f"{i+1}. [{dialogue['start']:.1f}s-{dialogue['end']:.1f}s]: {dialogue['text']}")
                        
                        with col2:
                            st.subheader("🇲🇲 မြန်မာပြန်များ")
                            for i, text in enumerate(burmese_dialogues[:5]):
                                st.write(f"{i+1}. {text}")
                        
                        st.subheader("🔊 မြန်မာအသံဥပမာ")
                        st.audio(final_audio_path, format="audio/wav")
                        
                        st.subheader("🎬 Dubbed Video Preview")
                        st.video(dubbed_video_path)
                        
                        # Download buttons
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            with open(final_audio_path, "rb") as f:
                                st.download_button(
                                    label="📥 မြန်မာအသံဖိုင်",
                                    data=f,
                                    file_name="movie_dubbing_audio.wav",
                                    mime="audio/wav"
                                )
                        
                        with col4:
                            with open(dubbed_video_path, "rb") as f:
                                st.download_button(
                                    label="📥 Dubbed Video",
                                    data=f,
                                    file_name="movie_burmese_dubbed.mp4",
                                    mime="video/mp4"
                                )
                        
                        # Cleanup
                        for segment in burmese_audio_segments:
                            if os.path.exists(segment):
                                os.remove(segment)
                        if os.path.exists(final_audio_path):
                            os.remove(final_audio_path)
                        if os.path.exists(dubbed_video_path):
                            os.remove(dubbed_video_path)
                
                # Clean original temp file
                if os.path.exists(video_path):
                    os.remove(video_path)
                    
            except Exception as e:
                st.error(f"❌ Dubbing process မှာ error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

st.markdown("---")
st.markdown("""
### 🎯 Dubbing System Features:
1. **လူပြောသံကို detect** - Whisper နဲ့ စကားပြောအပိုင်းတွေကို ဖော်ထုတ်
2. **Timing sync** - မူရင်းအချိန်နဲ့ ကိုက်ညီအောင်
3. **Context-aware translation** - ဇတ်လမ်းအလိုက် ပြန်ဆို
4. **Lip-sync attempt** - ပါးစပ်လှုပ်ရှားမှုနဲ့ နီးစပ်အောင်

### ⚠️ Limitations:
- Perfect lip-sync အတွက် AI voice cloning လိုအပ်တယ်
- Background music/sounds ကို preserve လုပ်ဖို့ ပိုအဆင့်မြင့်တယ်
- Multiple speakers အတွက် ခွဲခြားဖို့လိုတယ်
""")
