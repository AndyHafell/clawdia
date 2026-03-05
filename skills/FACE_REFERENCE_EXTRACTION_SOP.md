# Face Reference Extraction SOP

## Purpose

Extract high-quality face reference images from a video of thumbnail poses. These images are used by the Thumbnail System (`generate_thumbnail.py`) for AI face recognition when generating YouTube thumbnails.

## Prerequisites

- **FFmpeg** installed (`brew install ffmpeg`)
- Source video with multiple locked-in facial expressions/poses
- Video should be 1080p or higher for best quality

## Process

### Step 1: Extract Review Frames

Pull one frame every 7 seconds from the video for review:

```bash
mkdir -p face_extract_review

ffmpeg -i "path/to/video.mp4" \
  -vf "fps=1/7" \
  -q:v 2 \
  face_extract_review/frame_%03d.jpg
```

This creates JPG thumbnails for quick visual review. Adjust the `fps=1/7` value if you want more or fewer frames (e.g., `fps=1/3` for every 3 seconds).

### Step 2: Review and Select Best Frames

Go through all extracted frames and pick **10 frames** with the best variety of locked-in expressions. Look for:

- **Clear face visibility** (not blurred, not mid-transition)
- **Distinct expressions** (avoid duplicates of the same emotion)
- **Good framing** (face centered, well-lit)
- **Hands not blocking face** (unless the pose requires it)

Target expression variety:
1. Neutral/serious
2. Slight smile (talking/natural)
3. Surprised (eyes wide, mouth open "O")
4. Screaming/excited (mouth wide open)
5. Thinking/clever (finger on temple, smirk)
6. Confident (arms crossed, subtle smile)
7. Pointing + big smile
8. Bored/leaning (fist on cheek)
9. Confused/disgusted (scrunched face)
10. Hype/yelling (energetic close-up)

### Step 3: Export Selected Frames as High-Quality PNGs

For each selected frame, note its timestamp (frame_number x 7 seconds) and extract at full quality:

```bash
mkdir -p face_references_new

# Example: extract frame at timestamp 140s as PNG
ffmpeg -ss 140 -i "path/to/video.mp4" \
  -frames:v 1 -q:v 1 \
  face_references_new/04_screaming_excited.png
```

**Naming convention**: `XX_expression_name.png` (e.g., `01_neutral_serious.png`)

To extract all 10 in parallel for speed:

```bash
VIDEO="path/to/video.mp4"
OUT="face_references_new"

ffmpeg -y -ss 7 -i "$VIDEO" -frames:v 1 -q:v 1 "$OUT/01_neutral_serious.png" &
ffmpeg -y -ss 42 -i "$VIDEO" -frames:v 1 -q:v 1 "$OUT/02_slight_smile.png" &
ffmpeg -y -ss 133 -i "$VIDEO" -frames:v 1 -q:v 1 "$OUT/03_surprised.png" &
# ... add remaining frames
wait
```

### Step 4: Crop to Face Only

**IMPORTANT**: The face references must be FACE ONLY — no body, shoulders, or hands. Use `pipeline/crop_faces.py` to auto-detect the face and crop tightly (hair to chin, ear to ear).

```bash
# Run the crop script (reads from face_references_new/, writes to face_references/)
python3 pipeline/crop_faces.py
```

The script uses OpenCV Haar cascade face detection with tight padding:
- **Top**: 0.55x face height (forehead + hair)
- **Bottom**: 0.35x face height (chin + tiny bit of neck)
- **Left/Right**: 0.35x face width (ears)

Output is ~400-550px square face-only crops. This ensures the AI model focuses on facial features, not clothing or body.

### Step 5: Curate and Clean Up

1. Review the cropped faces in `face_references/`
2. Delete any that don't look right
3. Remove old/legacy face reference files (old `face_*.jpg`, `image*.png`, etc.)
4. Clean up temporary review frames:

```bash
rm -rf face_extract_review/
```

The `face_references/` folder should contain ONLY your curated face-only crops.

## Output

- **Location**: `face_references/` (used by thumbnail system)
- **Format**: PNG, ~400-550px square (face-only crops)
- **Count**: ~9 images per video (expandable)
- **Size**: ~130-210KB each

## Viral Thumbnail Selection

The thumbnail system (`generate_thumbnail.py`) pulls inspiration from the **Viral Videos** table in Airtable:

- Thumbnails are sorted by **Outlier Score** (highest first)
- The system filters with `NOT({Thumbnail Used})` to skip already-used thumbnails
- After each generation run, selected thumbnails are marked as **Thumbnail Used = True**
- If all thumbnails are used up, uncheck `Thumbnail Used` in the Viral Videos table to reuse them
- Each run picks randomly from the **top 10 unused** thumbnails

**IMPORTANT**: Always ensure fresh viral thumbnails are available. If generation results look repetitive, check the Viral Videos table — you may need to uncheck used thumbnails or add new viral inspiration.

## Notes

- The thumbnail system loads ALL images from `face_references/` automatically
- Face-only crops (no body) produce the best face likeness in generated thumbnails
- Re-run this process whenever you want to update your look (new haircut, different outfits, etc.)
- Video source should have a solid-color or blurred background for cleanest results
- Hair back vs hair down variations help the AI handle different styles
- The `pipeline/crop_faces.py` script can be re-run anytime to adjust crop padding
