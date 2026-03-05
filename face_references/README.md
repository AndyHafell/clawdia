# Face References

Add your face-only reference images here.

## Requirements
- **Face only** — hair to chin, ear to ear (no body, shoulders, or hands)
- **Multiple angles** — straight on, slight left, slight right
- **Good lighting** — consistent, well-lit
- **5-10 images** — more variety = better AI likeness
- **PNG format** — best quality for AI generation

## How to Create Face References

1. Record yourself on camera from multiple angles
2. Extract frames:
   ```bash
   ffmpeg -i your_video.mp4 -vf "fps=1" face_references_new/frame_%04d.png
   ```
3. Run the auto-cropper:
   ```bash
   python3 pipeline/crop_faces.py
   ```
4. Review crops in this folder — delete any bad ones

See `skills/FACE_REFERENCE_EXTRACTION_SOP.md` for the full SOP.
