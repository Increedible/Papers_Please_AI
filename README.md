# Papers Please AI

This project is an experiment in automating document checking inside the game *Papers, Please*.  
It uses Python with OpenCV, PyAutoGUI, PyQt5, and Tesseract OCR to capture the screen, read in-game documents, and overlay visual hints for mismatches.

## How it works
- **Screen capture**: Frames are taken from the game window using PyAutoGUI.  
- **OCR**: Text on documents (passport, entry permit, access permit, vaccination certificates) is read with Tesseract OCR.  
- **Image matching**: Country seals and document types are identified by template matching with OpenCV.  
- **Overlays**: PyQt5 draws transparent rectangles on top of the game window to highlight suspicious fields.  
- **Logic checks**: Scripts compare extracted details (expiry dates, issuing cities, ID numbers, etc.) against expected rules.

## Requirements
- Python 3  
- Tesseract OCR  
- Dependencies: `opencv-python`, `numpy`, `pytesseract`, `pyautogui`, `pywin32`, `PyQt5`

## Important
In `main.py`, the Tesseract path is **hardcoded**.  
Replace it with the path to your local `tesseract.exe` installation, for example:
pytesseract.pytesseract.tesseract_cmd = 'C:/path/to/Tesseract-OCR/tesseract.exe'  
os.environ["TESSDATA_PREFIX"] = "C:/path/to/Tesseract-OCR/tessdata/"

## Usage
1. Start *Papers, Please* in windowed mode at 1280x720 resolution.  
2. Run:  
   python main.py  
3. The overlay will appear. As documents are presented, squares highlight relevant fields and console output lists detected mismatches.

## Notes
- OCR accuracy depends heavily on resolution and trained Tesseract language files.  
- The project is a prototype and not a finished bot — expect errors and false positives.  
- For experimentation only; not affiliated with or endorsed by the creator of *Papers, Please*.
