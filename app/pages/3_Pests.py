
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys, datetime, hashlib, io, textwrap
from collections import Counter
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="pest_theme")
theme = "dark" if dark else "light"

PEST_CLASSES = [
    'rice leaf roller','rice leaf caterpillar','paddy stem maggot','asiatic rice borer','yellow rice borer',
    'rice gall midge','Rice Stemfly','brown plant hopper','white backed plant hopper','small brown plant hopper',
    'rice water weevil','rice leafhopper','grain spreader thrips','rice shell pest','grub','mole cricket','wireworm',
    'white margined moth','black cutworm','large cutworm','yellow cutworm','red spider','corn borer','army worm','aphids',
    'Potosiabre vitarsis','peach borer','english grain aphid','green bug','bird cherry-oataphid','wheat blossom midge',
    'penthaleus major','longlegged spider mite','wheat phloeothrips','wheat sawfly','cerodonta denticornis','beet fly',
    'flea beetle','cabbage army worm','beet army worm','Beet spot flies','meadow moth','beet weevil','sericaorient alismots chulsky',
    'alfalfa weevil','flax budworm','alfalfa plant bug','tarnished plant bug','Locustoidea','lytta polita','legume blister beetle',
    'blister beetle','therioaphis maculata Buckton','odontothrips loti','Thrips','alfalfa seed chalcid','Pieris canidia',
    'Apolygus lucorum','Limacodidae','Viteus vitifoliae','Colomerus vitis','Brevipoalpus lewisi McGregor','oides decempunctata',
    'Polyphagotars onemus latus','Pseudococcus comstocki Kuwana','parathrene regalis','Ampelophaga','Lycorma delicatula','Xylotrechus',
    'Cicadella viridis','Miridae','Trialeurodes vaporariorum','Erythroneura apicalis','Papilio xuthus','Panonchus citri McGregor',
    'Phyllocoptes oleiverus ashmead','Icerya purchasi Maskell','Unaspis yanonensis','Ceroplastes rubens','Chrysomphalus aonidum',
    'Parlatoria zizyphus Lucus','Nipaecoccus vastalor','Aleurocanthus spiniferus','Tetradacus c Bactrocera minax ','Dacus dorsalis(Hendel)',
    'Bactrocera tsuneonis','Prodenia litura','Adristyrannus','Phyllocnistis citrella Stainton','Toxoptera citricidus','Toxoptera aurantii',
    'Aphis citricola Vander Goot','Scirtothrips dorsalis Hood','Dasineura sp','Lawana imitata Melichar','Salurnis marginella Guerr',
    'Deporaus marginatus Pascoe','Chlumetia transversa','Mango flat beak leafhopper','Rhytidodera bowrinii white','Sternochetus frigidus',
    'Cicadellidae'
]
N = len(PEST_CLASSES)

# ── Pest management guide (detailed for top pests, generic for rest) ──
def get_pest_guide(pest_name):
    """Return detailed management guide for any pest."""
    guides = {
        "aphids": {
            "desc": "Small sap‑sucking insects that cluster on new growth and undersides of leaves. They weaken plants, cause leaf curling, and spread viruses.",
            "organic": "Neem oil spray (5ml/L water) every 7 days. Soap spray: 1 tbsp mild liquid soap in 1L water. Release ladybugs or lacewings.",
            "inorganic": "Imidacloprid 17.8% SL — 0.5ml/L water. Dimethoate 30% EC — 1ml/L water.",
            "admin": "Wear gloves and mask. Mix pesticide separately first. Target leaf undersides. Spray on calm days.",
            "timing": "Early morning or late afternoon. Apply at first sign of aphids. Repeat every 14 days if needed.",
            "prevention": "Plant marigolds and nasturtiums nearby. Rotate crops yearly. Encourage ladybugs with dill and fennel."
        },
        "army worm": {
            "desc": "Caterpillars that march across fields in large numbers, devouring grasses and crops overnight. Can destroy entire fields rapidly.",
            "organic": "Neem oil (5ml/L + 1ml soap). Bt spray (2g/L). Sprinkle wood ash into whorls.",
            "inorganic": "Emamectin benzoate 5% SG — 0.4g/L. Lambda‑cyhalothrin 5% EC — 1ml/L.",
            "admin": "Spray directly into whorls where larvae hide. Use flat‑fan nozzle. Wear full protective gear.",
            "timing": "Spray when 5% of plants show damage. Early morning or late evening when larvae are active.",
            "prevention": "Plant early to avoid peak season. Rotate with legumes. Use push‑pull technique with desmodium."
        },
        "rice leaf roller": {
            "desc": "Larvae fold leaf edges and feed inside, creating longitudinal white streaks. Heavy infestation turns fields yellowish.",
            "organic": "Neem oil (5ml/L) every 7-10 days. Bacillus thuringiensis (Bt) — 2g/L water. Encourage birds with field perches.",
            "inorganic": "Chlorantraniliprole 18.5% SC — 0.4ml/L. Cartap hydrochloride 50% SP — 1g/L.",
            "admin": "Mix in bucket first then pour into sprayer through strainer. Use flat‑fan nozzle for even coverage.",
            "timing": "Spray when 1-2 damaged leaves per hill are seen. Repeat after 15 days if needed.",
            "prevention": "Use resistant varieties like IR64, IR72. Avoid excessive nitrogen fertilizer. Keep bunds clean."
        },
        "corn borer": {
            "desc": "Larvae tunnel into stalks and ears, weakening plants and causing direct yield loss. Look for small holes and sawdust‑like frass.",
            "organic": "Bt spray (2g/L). Neem oil (5ml/L). Release Trichogramma wasps to parasitize eggs.",
            "inorganic": "Carbofuran 3G granules — 8kg/ha in whorls. Chlorpyrifos 20% EC — 2ml/L. Flubendiamide 20% WG — 0.5g/L.",
            "admin": "For granules: wear gloves, place 3-4 granules into each whorl. For sprays: target stalks and leaf axils.",
            "timing": "Apply granules 3-4 weeks after planting. Spray when moths seen or first pinholes appear.",
            "prevention": "Plant Bt‑maize varieties. Burn crop residues after harvest. Deep plough to expose pupae."
        },
        "fall armyworm": {
            "desc": "Caterpillars feed on leaves, whorls, and ears of maize. Can destroy entire field in days. Look for window pane damage.",
            "organic": "Neem oil (5ml/L + 1ml soap). Bt spray (2g/L). Chilli‑garlic spray. Wood ash in whorls.",
            "inorganic": "Emamectin benzoate 5% SG — 0.4g/L. Spinetoram 11.7% SC — 0.5ml/L. Lambda‑cyhalothrin 5% EC — 1ml/L.",
            "admin": "Direct spray into whorls. Mix powder formulations into paste first then dilute. Spray when larvae are young.",
            "timing": "Scout weekly. Spray when 5% plants show damage. Early morning or late evening best.",
            "prevention": "Plant early. Rotate with legumes. Push‑pull: plant desmodium between rows and napier grass around field."
        }
    }
    
    # Look for partial matches
    pest_lower = pest_name.lower()
    for key, guide in guides.items():
        if key in pest_lower or pest_lower in key:
            return guide
    
    # Generic guide for all other pests
    return {
        "desc": f"The {pest_name} is a crop pest that damages plants by feeding on leaves, stems, or fruits. Early detection and proper management are essential to prevent economic losses.",
        "organic": f"Neem oil spray (5ml/L water) applied every 7 days. Insecticidal soap (1 tbsp/L water). Encourage natural predators by planting diverse crops. Hand‑pick larger insects when populations are low.",
        "inorganic": f"Contact your local agricultural extension officer for specific chemical recommendations based on the crop affected and infestation level. Common options may include pyrethroid or organophosphate insecticides at recommended dosages.",
        "admin": f"Always wear protective clothing, gloves, and a mask when handling pesticides. Mix in a well‑ventilated area. Follow label instructions precisely. Never mix different chemicals unless specified. Calibrate sprayer for correct application rate.",
        "timing": f"Apply at first sign of infestation. Spray early morning or late evening when beneficial insects are less active. Avoid spraying before rain or when wind speed exceeds 8 km/h. Repeat application as recommended on the product label.",
        "prevention": f"Practice crop rotation with non‑host crops. Use resistant varieties when available. Maintain field hygiene by removing crop residues. Scout fields weekly for early detection. Encourage natural enemies by reducing broad‑spectrum pesticide use."
    }




def strip_emoji(text):
    """Remove emoji characters that PDF libraries cannot render."""
    import re
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f900-\U0001f9ff"
        u"\U0001FA00-\U0001FA6F"
        u"\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)


def generate_pdf_report(pest_name, confidence, guide):
    """Generate a professionally designed PDF using reportlab (Unicode‑safe)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, textColor=HexColor('#ffffff'), alignment=TA_CENTER, spaceAfter=4)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=9, textColor=HexColor('#ffffff'), alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=8)
    pest_name_style = ParagraphStyle('PestName', parent=styles['Normal'], fontSize=18, spaceAfter=4)
    confidence_style = ParagraphStyle('Confidence', parent=styles['Normal'], fontSize=12, spaceAfter=10)
    
    story = []
    
    # Header table with orange background
    header_data = [[
        Paragraph("GAIA Pest Diagnosis Report", title_style)
    ], [
        Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')} | Powered by Darkmoor Ltd", subtitle_style)
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#ff9800')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10*mm))
    
    # Pest identification
    story.append(Paragraph("Pest Identified", section_style))
    story.append(Paragraph(pest_name.title(), pest_name_style))
    story.append(Paragraph(f"Confidence: {confidence:.1f}%", confidence_style))
    story.append(Spacer(1, 5*mm))
    
    # Sections with coloured backgrounds
    sections = [
        ("About This Pest", guide['desc'], '#fff3e0', '#e65100'),
        ("Organic Control Methods", guide['organic'], '#e8f5e9', '#2e7d32'),
        ("Inorganic (Chemical) Control", guide['inorganic'], '#fff3e0', '#e65100'),
        ("How to Administer", guide['admin'], '#e3f2fd', '#1565c0'),
        ("When to Apply", guide['timing'], '#f3e5f5', '#6a1b9a'),
        ("Prevention Tips", guide['prevention'], '#fff9c4', '#f57f17'),
    ]
    
    for title, text, bg, fg in sections:
        sec_data = [[Paragraph(f"<font color='{fg}'>{title}</font>", section_style)], [Paragraph(strip_emoji(text), body_style)]]
        sec_table = Table(sec_data, colWidths=[170*mm])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 4*mm))
    
    # Footer
    story.append(Spacer(1, 8*mm))
    footer_text = Paragraph("<font color='#999999'>Generated by GAIA — Global Agricultural Intelligence Assistant<br/>darkmoorltd@gmail.com | Powered by Darkmoor Ltd</font>", styles['Normal'])
    story.append(footer_text)
    
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
    """Generate a professionally designed PDF report."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ── Header ──
    pdf.set_fill_color(255, 152, 0)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 18, "GAIA Pest Diagnosis Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')} | Powered by Darkmoor Ltd", ln=True, align="C")
    pdf.ln(12)
    
    # ── Pest Identification ──
    pdf.set_text_color(230, 81, 0)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Pest Identified", ln=True)
    pdf.set_draw_color(255, 152, 0)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, pest_name.title(), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Confidence: {confidence:.1f}%", ln=True)
    pdf.ln(6)
    
    # ── About This Pest ──
    pdf.set_fill_color(255, 243, 224)
    pdf.set_text_color(230, 81, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "About This Pest", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(255, 243, 224)
    pdf.multi_cell(0, 6, strip_emoji(guide['desc']), fill=True)
    pdf.ln(4)
    
    # ── Organic Control ──
    pdf.set_fill_color(232, 245, 233)
    pdf.set_text_color(46, 125, 50)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Organic Control Methods", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(232, 245, 233)
    pdf.multi_cell(0, 6, strip_emoji(guide['organic']), fill=True)
    pdf.ln(4)
    
    # ── Inorganic Control ──
    pdf.set_fill_color(255, 243, 224)
    pdf.set_text_color(230, 81, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Inorganic (Chemical) Control", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(255, 243, 224)
    pdf.multi_cell(0, 6, strip_emoji(guide['inorganic']), fill=True)
    pdf.ln(4)
    
    # ── Administration ──
    pdf.set_fill_color(227, 242, 253)
    pdf.set_text_color(21, 101, 192)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "How to Administer", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(227, 242, 253)
    pdf.multi_cell(0, 6, strip_emoji(guide['admin']), fill=True)
    pdf.ln(4)
    
    # ── Timing ──
    pdf.set_fill_color(243, 229, 245)
    pdf.set_text_color(106, 27, 154)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "When to Apply", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(243, 229, 245)
    pdf.multi_cell(0, 6, strip_emoji(guide['timing']), fill=True)
    pdf.ln(4)
    
    # ── Prevention ──
    pdf.set_fill_color(255, 249, 196)
    pdf.set_text_color(245, 127, 23)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Prevention Tips", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(255, 249, 196)
    pdf.multi_cell(0, 6, strip_emoji(guide['prevention']), fill=True)
    pdf.ln(8)
    
    # ── Footer ──
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "Generated by GAIA — Global Agricultural Intelligence Assistant", ln=True, align="C")
    pdf.cell(0, 6, "darkmoorltd@gmail.com | Powered by Darkmoor Ltd", ln=True, align="C")
    
    # Return as bytes
    return pdf.output(dest="S").encode("latin-1")

def save_feedback(image_name, predicted_class, helpful):
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    try: supabase.table("user_feedback").insert({"user_id": st.session_state.user.id, "image_name": image_name, "predicted_class": predicted_class, "helpful": helpful, "created_at": datetime.datetime.now().isoformat()}).execute()
    except: pass

def deduct_one_scan():
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try: supabase.table("user_scans").update({"scans_remaining": supabase.raw("scans_remaining - 1")}).eq("user_id", uid).execute()
    except: supabase.rpc("decrement_scan", {"uid": uid}).execute()
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", uid).execute()
    if res.data: st.success(f"Scan deducted. Remaining scans: {res.data[0]['scans_remaining']}")

if theme == "dark":
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#1a0f00,#2e1c00,#3e2a00,#1a0f00);color:#fff8e1}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#ff9800,#ffcc80,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(255,152,0,.7);animation:pestGlow 2s ease-in-out infinite alternate}@keyframes pestGlow{from{text-shadow:0 0 25px rgba(255,152,0,.7)}to{text-shadow:0 0 50px rgba(255,152,0,1),0 0 80px rgba(255,152,0,.6)}}.subtitle{text-align:center;font-size:1.2rem;color:#bcaaa4}.result-card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #ff9800;box-shadow:0 0 30px rgba(255,152,0,.3)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#e65100,#ff9800,#e65100);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 10px rgba(230,81,0,.3);animation:pestGlowLight 2s ease-in-out infinite alternate}@keyframes pestGlowLight{from{text-shadow:0 0 10px rgba(230,81,0,.3)}to{text-shadow:0 0 25px rgba(230,81,0,.8),0 0 50px rgba(230,81,0,.5)}}.subtitle{text-align:center;font-size:1.2rem;color:#4e342e}.result-card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #e65100;box-shadow:0 0 20px rgba(230,81,0,.2)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>""", unsafe_allow_html=True)

st.markdown('<div class="title">🐛 Pest Detection & Management</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Snap a photo — get identification, organic & chemical control methods, and a downloadable PDF report</div>', unsafe_allow_html=True)

with st.expander("📸 How to take a good insect photo"):
    st.markdown("1. 🔍 Get as close as possible while keeping the insect in focus.\n2. 📱 Hold phone steady.\n3. ☀️ Good lighting is essential.\n4. 📤 Upload 2‑3 photos for better results.")

files = st.file_uploader("📤 Upload insect photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        from app.utils.download_models import ensure_model
        
        # Force delete old file to ensure fresh download
        cp_path = os.path.join("checkpoints", "pests_102class", "model.pt")
        if os.path.exists(cp_path):
            os.remove(cp_path)
        
        cp = ensure_model("pests_102class")
        if cp and os.path.exists(cp):
            try:
                model = create_model_from_checkpoint(cp, N)
            except:
                if os.path.exists(cp_path):
                    os.remove(cp_path)
                raise
    except Exception as e: st.warning(f"Real model unavailable, using demo. ({e})")

    predictions = []
    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐛 {f.name}", expanded=True):
            c1, c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model:
                t = Compose([Resize((224,224)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad(): probs = F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
            else:
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(N); probs/=probs.sum()
            top_idx = np.argmax(probs)
            pest_name = PEST_CLASSES[top_idx]
            confidence = probs[top_idx]*100
            predictions.append(pest_name)
            
            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid #ff9800;"><h2 style="margin:0">{pest_name.title()} <span style="font-size:1.5rem;color:#ff9800">{confidence:.1f}%</span></h2></div>', unsafe_allow_html=True)
            for i in np.argsort(probs)[::-1][1:5]:
                c2.write(f"**{PEST_CLASSES[i].title()}**: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            deduct_one_scan()
                
            # ===== DEEPSEEK EXPLANATION + VOICE =====
            if model is not None:
                with st.spinner("🧠 GAIA is preparing your pest management guide..."):
                    try:
                        from app.utils.deepseek_explainer import explain_diagnosis, text_to_speech
                        
                        top_pest = PEST_CLASSES[top_idx]
                        explanation, explain_err = explain_diagnosis(top_pest, probs[top_idx] * 100, "various crops", "pest")
                        
                        if explanation:
                            with st.expander("📋 Complete Pest Management Guide (AI-Generated)", expanded=True):
                                st.markdown(explanation)
                                
                                if st.button("🔊 Listen to Pest Guide", key=f"voice_{f.name}"):
                                    with st.spinner("🔊 Generating voice..."):
                                        audio_bytes, tts_err = text_to_speech(explanation[:2000])
                                        if audio_bytes:
                                            st.audio(audio_bytes, format="audio/mp3")
                                        else:
                                            st.warning(f"Voice unavailable: {tts_err}")
                    except Exception as e:
                        st.warning(f"Pest guide unavailable: {str(e)[:100]}")
            
            # Feedback
            col_fb1, col_fb2 = c2.columns(2)
            if col_fb1.button("👍 Helpful", key=f"pest_help_{f.name}"): save_feedback(f.name, pest_name, True); col_fb1.success("Thanks!")
            if col_fb2.button("👎 Not", key=f"pest_not_{f.name}"): save_feedback(f.name, pest_name, False); col_fb2.info("We'll improve.")
            
            # Generate management guide and PDF
            guide = get_pest_guide(pest_name)
            pdf_bytes = generate_pdf_report(pest_name, confidence, guide)
            
            # Show summary
            with st.expander("📋 Pest Management Summary", expanded=False):
                st.markdown(f"**📖 About:** {strip_emoji(guide['desc'])}")
                st.markdown(f"**🌿 Organic:** {strip_emoji(guide['organic'])}")
                st.markdown(f"**🧪 Chemical:** {strip_emoji(guide['inorganic'])}")
                st.markdown(f"**💉 How to Apply:** {strip_emoji(guide['admin'])}")
                st.markdown(f"**⏰ Timing:** {strip_emoji(guide['timing'])}")
                st.markdown(f"**🛡️ Prevention:** {strip_emoji(guide['prevention'])}")
            
            # PDF download button
            st.download_button(
                label=f"📥 Download PDF Report — {pest_name.title()}",
                data=pdf_bytes,
                file_name=f"GAIA_{pest_name.replace(' ', '_')}_Report.pdf",
                mime="application/pdf",
                help="Download a professionally designed PDF report with all management details."
            )

    if len(predictions) >= 2:
        vote = Counter(predictions).most_common(1)[0]
        if vote[1] > len(predictions)//2:
            st.success(f"🗳️ Majority vote: **{vote[0].title()}** ({vote[1]}/{len(predictions)} photos)")

# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[7]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")