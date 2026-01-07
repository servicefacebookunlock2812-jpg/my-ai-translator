import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os
import re

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Universal AI Translator", page_icon="🌐")
st.title("🌐 Universal AI Video Translator")

@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

model = load_whisper()

def clean_myanmar_text(text):
    """မြန်မာစာသားကို သန့်ရှင်းပြီး စာကြောင်းတစ်ခုစီကို သပ်သပ်ရပ်ရပ် ဖြစ်အောင်လုပ်ပေးခြင်း"""
    # ပိုက်ဆံထူးတွေကို ဖယ်ရှားခြင်း
    text = re.sub(r'[၊။]+', lambda m: m.group() + ' ', text)
    # အပိုဖြည့်စွက်ခြင်း
    text = text.replace("  ", " ")
    return text.strip()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က အဆင့်မြင့် Model သစ်ဖြင့် ဘာသာပြန်နေပါတယ်...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၁။ အသံကို စာသားပြောင်း
                result = model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')
                
                st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                # ၂။ Groq Llama 3.3 နဲ့ မြန်မာလို ပြန်ဆို (ပိုပြီး natural ဖြစ်အောင် prompt update)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": """မင်းက professional Burmese translator နဲ့ narrator တစ်ယောက်ဖြစ်တယ်။ 
                        ဘာသာပြန်တဲ့အခါ အချက်အလက်တွေကို တိတိကျကျပေးရမယ်၊ 
                        စကားပြောသလို ချောမွေ့ပြီး နားထောင်ရလွယ်အောင်ပြန်ရမယ်။ 
                        စာကြောင်းတွေကို သပ်သပ်ရပ်ရပ် ခွဲပေးပါ။ 
                        အဓိပ္ပာယ်တူသော မြန်မာစကားလုံးတွေကို သုံးပါ။
                        ဘာသာပြန်ချက်တစ်ခုတည်းကိုပဲ ပြန်ပေးပါ။"""},
                        {"role": "user", "content": f"""ဒီ {detected_lang} စာသားကို မြန်မာလိုပြန်ပေးပါ။ 
                        သတိထားရမှာက: 
                        1. တိတိကျကျပြန်ပါ
                        2. နားထောင်ရလွယ်အောင် ချောချောမွေ့မွေ့ပြန်ပါ
                        3. စာကြောင်းတွေကို သပ်သပ်ရပ်ရပ် ခွဲပါ
                        
                        စာသား: {original_text}"""}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                mm_text = completion.choices[0].message.content
                
                # စာသားကို သန့်ရှင်းအောင်လုပ်ခြင်း
                mm_text = clean_myanmar_text(mm_text)
                
                # ၃။ မြန်မာ AI အသံထုတ် (narrator လို natural ဖြစ်အောင်)
                output_audio = "final_voice.mp3"
                communicate = edge_tts.Communicate(
                    mm_text, 
                    "my-MM-ThihaNeural",
                    rate="+10%",  # နည်းနည်းမြန်အောင်
                    pitch="+2Hz"  # သဘာဝကျအောင်
                )
                asyncio.run(communicate.save(output_audio))

                st.success("✅ ဘာသာပြန်ခြင်း ပြီးပါပြီ!")
                
                st.subheader("📝 မြန်မာစာသား (Script)")
                st.text_area("ဘာသာပြန်ထားသော စာသား", mm_text, height=200)
                
                st.subheader("🔊 AI Narrator အသံ")
                st.audio(output_audio)
                
                # ဒေါင်းလုဒ်လုပ်လို့ရအောင်
                with open(output_audio, "rb") as file:
                    btn = st.download_button(
                        label="အသံဖိုင်ကို ဒေါင်းလုဒ်ရယူမယ်",
                        data=file,
                        file_name="myanmar_translation.mp3",
                        mime="audio/mp3"
                    )
                
                os.remove(video_path)
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                    
            except Exception as e:
                st.error(f"❌ Error ဖြစ်သွားပါတယ်: {str(e)}")
                st.info("ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ထပ်စမ်းကြည့်ပါ။")

st.markdown("---")
st.markdown("""
**📌 သတိပြုရန်:**
- ဗီဒီယိုဖိုင်အရွယ်အစားကို 100MB အောက်ထားပါ
- အသံရှင်းလင်းမှ ပိုကောင်းပါတယ်
- ဘာသာပြန်ချိန် ဖိုင်အရွယ်အစားပေါ်မူတည်ပါတယ်
""")
