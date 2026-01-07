import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os
import re
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import subprocess

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="AI Video Dubbing", page_icon="🎬")
st.title("🎬 AI Video Dubbing - ဇတ်ကားအသံပြောင်း")
st.markdown("**ဇတ်ကားထဲက ဇာတ်ဆောင်အသံတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးမယ်**")

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def extract_audio_from_video(video_path, audio_output="extracted_audio.wav"):
    """FFmpeg သုံးပြီး video ကနေ audio ထုတ်ယူ"""
    try:
        cmd = [
            'ffmpeg', '-i', video_path,
            '-q:a', '0', '-map', 'a',
            '-y', audio_output
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return audio_output
        else:
            # Alternative method using pydub if ffmpeg not available
            st.warning("FFmpeg မတွေ့ပါ။ အခြားနည်းလမ်းဖြင့် ဆက်လုပ်ပါမည်။")
            return None
    except Exception as e:
        st.warning(f"FFmpeg error: {str(e)}")
        return None

def create_sync_burmese_audio(original_audio_path, translated_text, timestamps):
    """မြန်မာအသံကို sync လုပ်ပြီး ထုတ်ပေးခြင်း"""
    try:
        # Load original audio to get duration
        original_audio = AudioSegment.from_file(original_audio_path)
        
        # Create silent audio of same length
        silent_audio = AudioSegment.silent(duration=len(original_audio))
        
        # Generate Burmese TTS
        tts_output = "burmese_tts_temp.mp3"
        communicate = edge_tts.Communicate(
            text=translated_text,
            voice="my-MM-ThihaNeural",
            rate="+5%",
            pitch="+1Hz"
        )
        asyncio.run(communicate.save(tts_output))
        
        burmese_audio = AudioSegment.from_mp3(tts_output)
        
        # For simplicity, we'll just overlay the burmese audio
        # In production, you'd need to split by timestamps
        final_audio = original_audio.overlay(burmese_audio)
        
        # Save final audio
        final_output = "synced_burmese_audio.wav"
        final_audio.export(final_output, format="wav")
        
        # Cleanup
        if os.path.exists(tts_output):
            os.remove(tts_output)
            
        return final_output
        
    except Exception as e:
        st.error(f"Audio sync error: {str(e)}")
        return None

# Streamlit UI
uploaded_file = st.file_uploader("ဇတ်ကား/ဗီဒီယို ဖိုင်တင်ပေးပါ", 
                                type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav'])

if uploaded_file is not None:
    # Show video preview
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext in ['mp4', 'mov', 'avi', 'mkv']:
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎤 စကားသံများကို ဖော်ထုတ်မယ်"):
            with st.spinner('ဇတ်ကားထဲက စကားသံတွေကို ဖော်ထုတ်နေပါတယ်...'):
                try:
                    # Save uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tfile:
                        tfile.write(uploaded_file.read())
                        media_path = tfile.name
                    
                    # Extract audio if video
                    audio_path = None
                    if file_ext in ['mp4', 'mov', 'avi', 'mkv']:
                        audio_path = "temp_audio.wav"
                        # Simple audio extraction using pydub
                        try:
                            from pydub import AudioSegment
                            video = AudioSegment.from_file(media_path)
                            video.export(audio_path, format="wav")
                        except:
                            # Fallback: use the original file if audio extraction fails
                            audio_path = media_path
                    else:
                        audio_path = media_path
                    
                    # Transcribe
                    result = model.transcribe(
                        audio_path,
                        language=None,
                        task="transcribe",
                        verbose=False
                    )
                    
                    # Store in session state
                    st.session_state['original_text'] = result['text']
                    st.session_state['segments'] = result.get('segments', [])
                    st.session_state['media_path'] = media_path
                    st.session_state['audio_path'] = audio_path
                    
                    # Show results
                    st.success(f"✅ စကားပြောအပိုင်း {len(result.get('segments', []))} ပိုင်းတွေ့ရှိပြီ")
                    
                    with st.expander("🔍 ဖော်ထုတ်ထားသော စကားသံများ"):
                        for i, segment in enumerate(result.get('segments', [])[:10]):  # Show first 10
                            st.write(f"{i+1}. [{segment['start']:.1f}s-{segment['end']:.1f}s]: {segment['text']}")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🇲🇲 မြန်မာလို အသံပြောင်းမယ်"):
            if 'original_text' not in st.session_state:
                st.warning("ကျေးဇူးပြု၍ စကားသံများကို အရင်ဖော်ထုတ်ပါ")
            else:
                with st.spinner('မြန်မာလို ဘာသာပြန်ပြီး အသံထုတ်နေပါတယ်...'):
                    try:
                        # Translate to Burmese
                        original_text = st.session_state['original_text']
                        
                        completion = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": """မင်းက ရုပ်ရှင်ဒါရိုက်တာနဲ့ ဘာသာပြန်ဆရာဖြစ်တယ်။ 
                                ဇတ်ကားထဲက ဇာတ်ဆောင်တွေပြောတဲ့ စကားကို မြန်မာလို dubbing အတွက် ပြန်ပေးရမယ်။
                                
                                သတိထားရမှာတွေ:
                                1. ရုပ်ရှင်ထဲမှာ ပြောသလို သဘာဝကျကျပြန်ပါ
                                2. အတိုချုံးပြီး ထိရောက်အောင်ပြန်ပါ
                                3. မြန်မာပရိသတ်နားလည်အောင် ပြန်ပါ"""},
                                {"role": "user", "content": f"ဒီစကားကို မြန်မာရုပ်ရှင် dubbing အတွက် ပြန်ပေးပါ: {original_text}"}
                            ],
                            temperature=0.7,
                            max_tokens=2000
                        )
                        
                        translated_text = completion.choices[0].message.content
                        
                        # Store in session state
                        st.session_state['translated_text'] = translated_text
                        
                        # Generate Burmese TTS
                        output_audio = "burmese_dubbing.mp3"
                        communicate = edge_tts.Communicate(
                            translated_text,
                            "my-MM-ThihaNeural",
                            rate="+5%",
                            pitch="+1Hz"
                        )
                        asyncio.run(communicate.save(output_audio))
                        
                        # Show results
                        st.success("✅ မြန်မာအသံပြောင်းပြီးပါပြီ!")
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.subheader("မူရင်းစကား")
                            st.text_area("Original", original_text[:500] + "..." if len(original_text) > 500 else original_text, 
                                       height=200, label_visibility="collapsed")
                        
                        with col_b:
                            st.subheader("မြန်မာပြန်")
                            st.text_area("Translated", translated_text[:500] + "..." if len(translated_text) > 500 else translated_text,
                                       height=200, label_visibility="collapsed")
                        
                        st.subheader("🔊 မြန်မာအသံ (Dubbing)")
                        st.audio(output_audio)
                        
                        # Download buttons
                        st.download_button(
                            label="📥 မြန်မာအသံဖိုင်ရယူရန်",
                            data=open(output_audio, "rb"),
                            file_name="movie_dubbing_burmese.mp3",
                            mime="audio/mp3"
                        )
                        
                        # Cleanup
                        if os.path.exists(output_audio):
                            os.remove(output_audio)
                        if 'media_path' in st.session_state and os.path.exists(st.session_state['media_path']):
                            os.remove(st.session_state['media_path'])
                        if 'audio_path' in st.session_state and os.path.exists(st.session_state['audio_path']):
                            os.remove(st.session_state['audio_path'])
                            
                    except Exception as e:
                        st.error(f"Translation/Audio error: {str(e)}")

# Instructions
st.markdown("---")
st.markdown("""
### 📋 ညွှန်ကြားချက်များ:

**ပထမအဆင့်:** "🎤 စကားသံများကို ဖော်ထုတ်မယ်" ကိုနှိပ်ပါ
**ဒုတိယအဆင့်:** "🇲🇲 မြန်မာလို အသံပြောင်းမယ်" ကိုနှိပ်ပါ

### ⚠️ သတိပြုရန်:
1. **အသံရှင်းသော ဗီဒီယိုများကိုသာ အသုံးပြုပါ**
2. **တစ်ကြိမ်လျှင် ၅ မိနစ်ထက် မပိုစေရ**
3. **အင်တာနက်အဆင်ပြေရန် လိုအပ်ပါသည်**

### 🛠️ Requirements များထည့်ရန်:
```bash
pip install streamlit openai-whisper groq edge-tts pydub
