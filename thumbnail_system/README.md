# 🎨 Thumbnail System

AI-powered YouTube thumbnail generation with template references and Nano Banana Pro.

---

## 📁 Folder Structure

```
thumbnail_system/
├── README.md                      ← You are here
├── config.py                      ← Configuration & API keys
├── generate_thumbnail.py          ← Main thumbnail generator
├── thumbnail_templates/      ← 📌 your template thumbnails (style references)
│   ├── Thumbnail_A_5VideosDay_NoWork.png
│   ├── Thumbnail_B_5VideosDay_Automated.png
│   └── Thumbnail_C_IDontMakeContent.png
├── produced_thumbnails/           ← 🎨 AI-generated output thumbnails
│   └── (Generated thumbnails appear here)
├── output/                        ← Legacy output folder (will phase out)
├── competitor_thumbnails/         ← Competitor reference thumbnails
├── templates/                     ← Template definitions
└── __pycache__/                   ← Python cache
```

---

## 🎯 What Each Folder Does

### `thumbnail_templates/`
**Purpose**: Store your template thumbnails for style reference

**Usage**:
- These are **style references** for AI generation
- AI will analyze these and create similar styles
- Add more templates here over time
- Used with `--competitor-ref` flag

**Example**:
```bash
python3 generate_thumbnail.py "My Video Title" \
  --competitor-ref "thumbnail_templates/Thumbnail_A_5VideosDay_NoWork.png" \
  --model pro
```

### `produced_thumbnails/`
**Purpose**: Store AI-generated output thumbnails

**Usage**:
- All AI-generated thumbnails save here
- Organized by timestamp and video title
- **This is where YouTube upload script finds thumbnails**
- Clean out old ones periodically

**Structure**:
```
produced_thumbnails/
└── 20260217_120000_My_Video_Title/
    ├── option_A.png
    ├── option_B.png
    └── option_C.png
```

### `output/`
**Purpose**: Legacy output folder (being phased out)

**Status**: Will eventually merge into `produced_thumbnails/`

### `competitor_thumbnails/`
**Purpose**: Store competitor thumbnails for style analysis

**Usage**:
- Download successful competitor thumbnails
- Use as style references
- Analyze what works

---

## 🚀 Quick Start

### Generate 3 Thumbnails
```bash
cd thumbnail_system
python3 generate_thumbnail.py "My Amazing Video Title" --model pro
```

**Output**: 3 thumbnails in `produced_thumbnails/[timestamp]_My_Amazing_Video_Title/`

### Use your Template as Reference
```bash
python3 generate_thumbnail.py "5 Videos Daily Tutorial" \
  --competitor-ref "thumbnail_templates/Thumbnail_B_5VideosDay_Automated.png" \
  --model pro
```

### Generate with Specific Style
```bash
python3 generate_thumbnail.py "My Video" --style "Face Left + Text Right" --model pro
```

---

## ⚙️ Configuration

### Edit `config.py` to change:
- Output directories
- Thumbnail dimensions (default: 1920x1080)
- Number of options to generate (default: 3)
- Gemini API model

### Current Settings
```python
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
NUM_OPTIONS = 3
NANO_BANANA_MODEL = "gemini-2.0-flash-exp-image-generation"
TEMPLATES_DIR = "thumbnail_templates"
PRODUCED_THUMBNAILS_DIR = "produced_thumbnails"
```

---

## 🎨 Workflow

### Standard Workflow
1. Run `generate_thumbnail.py` with video title
2. AI generates 3 options (A, B, C)
3. Thumbnails saved to `produced_thumbnails/`
4. YouTube upload script uses these automatically
5. Thumbnails stored in Airtable as attachments

### With Template Reference
1. Choose a template from `thumbnail_templates/`
2. Run with `--competitor-ref` flag pointing to template
3. AI analyzes style and creates similar design
4. Output saved to `produced_thumbnails/`

---

## 🔧 Integration with YouTube Publisher

The YouTube publisher (`../youtube_publisher.py`) automatically:
1. Calls `generate_thumbnails()` from this system
2. Gets 3 thumbnail options (A, B, C)
3. Uploads video with Option A
4. Stores all 3 options in Airtable
5. Creates Google Drive shareable links
6. User can download from Airtable for Test & Compare

---

## 📊 Face References

Add your face photos to improve AI thumbnails:

```bash
# Add photos to this folder:
../face_references/

# Supported formats:
- .jpg, .jpeg
- .png
- .webp

# AI will use these to generate thumbnails with your face
```

---

## 💡 Tips

### For Best Results:
- Use clear, high-resolution face photos
- Add multiple face angles to face_references/
- Use Nano Banana Pro (`--model pro`) for better quality
- Reference successful templates from `thumbnail_templates/`
- Keep thumbnail titles short and punchy

### Template Organization:
- Name templates descriptively
- Group by style (e.g., "face_left", "text_dominant", etc.)
- Keep best performers in `thumbnail_templates/`
- Remove underperforming styles

---

## 🎯 Next Steps

1. **Add Face Photos**: Put your photos in `../face_references/`
2. **Test Generation**: Run a test thumbnail generation
3. **Analyze Output**: Check `produced_thumbnails/` for results
4. **Add More Templates**: Save successful thumbnails as new templates
5. **Integrate**: Let YouTube publisher use this automatically

---

## 📚 Related Documentation

- [Thumbnail System Guide](../THUMBNAIL_SYSTEM_GUIDE.md) - Complete overview
- [YouTube Upload Guide](../YOUTUBE_UPLOAD_GUIDE.md) - Upload workflow
- [Airtable Attachments Setup](../AIRTABLE_ATTACHMENTS_SETUP.md) - Drive API setup

---

**Questions?** Check the parent folder's documentation or run:
```bash
python3 generate_thumbnail.py --help
```
