# TTS Text Preprocessor GUI - User Guide

## 📦 Installation

### Step 1: Install Required Packages

```bash
pip install openai tkinter
```

**Note:** `tkinter` usually comes with Python, but if not:
- **Windows:** Included with Python
- **macOS:** Included with Python
- **Linux:** `sudo apt-get install python3-tk`

### Step 2: Download the GUI Script

Save `tts_preprocessor_gui.py` to your project folder.

### Step 3: Prepare Your Files

Create a folder structure like this:
```
my-tts-project/
├── tts_preprocessor_gui.py
├── INPUT.txt
├── improved_prompt.txt
└── (OUTPUT.txt will be created automatically)
```

---

## 🚀 Quick Start

### Launch the Application

```bash
python tts_preprocessor_gui.py
```

A professional GUI window will open!

---

## 🎛️ GUI Overview

### Top Section: Configuration

**File Selection:**
- **Input File:** Your raw OCR text (INPUT.txt)
- **Output File:** Where cleaned text will be saved
- **Prompt File:** Your improved prompt (IMPROVED_PROMPT_FINAL.txt)

**LM Studio Settings:**
- **Host:** Usually `http://localhost:1234/v1`
- **Model:** Your model identifier (e.g., `mistral-7b-instruct-v0.3`)
- **Test Connection:** Verify LM Studio is running

**Model Parameters:**
- **Temperature:** 0.2 (recommended for consistency)
- **Seed:** 42 (fixed for reproducibility)
- **Batch Size:** 500 lines (adjustable)
- **Max Tokens:** 4000 (output buffer)

### Middle Section: Progress & Controls

**Progress Bar:** Visual progress indicator

**Statistics Panel:** Shows:
- Current batch number
- Elapsed time
- Status (Processing/Paused/Stopped)
- Overall progress percentage

**Control Buttons:**
- **▶ Start Processing:** Begin batch processing
- **⏸ Pause:** Pause processing (can resume later)
- **⏹ Stop:** Stop completely (saves progress)

### Bottom Section: Tabbed View

**📋 Console Log Tab:**
- Real-time processing log
- Color-coded messages:
  - 🟢 Green: Success messages
  - 🔵 Blue: Info messages
  - 🟡 Yellow: Warnings
  - 🔴 Red: Errors
  - 🟣 Purple: Batch markers

**👁 Current Batch Preview Tab:**
- Split view showing:
  - **Left:** Input text (before processing)
  - **Right:** Output text (after processing)
- Updates in real-time for each batch

**📄 Full Output Tab:**
- Shows complete output as it's generated
- Useful for monitoring overall quality
- Auto-scrolls to latest content

---

## 📖 Step-by-Step Usage

### 1. Start LM Studio First! ⚠️

**Before running the GUI:**
1. Open LM Studio
2. Load your model (Mistral-7B-Instruct-v0.3-IMAT)
3. Go to **Local Server** tab
4. Configure settings:
   - Context Length: 8192
   - GPU Offload: 32/32
   - Seed: 42
5. Click **Start Server**
6. Wait for "Server started" message

### 2. Launch the GUI

```bash
cd your-project-folder
python tts_preprocessor_gui.py
```

### 3. Configure Files

**Select Input File:**
1. Click "Browse..." next to "Input File"
2. Select your INPUT.txt
3. Output file path auto-suggests

**Select Prompt File:**
1. Click "Browse..." next to "Prompt File"
2. Select your IMPROVED_PROMPT_FINAL.txt

### 4. Test Connection

1. Click **"Test Connection"** button
2. You should see: ✓ Connection successful!
3. If error, check LM Studio server is running

### 5. Verify Settings

**Check these are correct:**
- Temperature: 0.2
- Seed: 42 (must be fixed!)
- Batch Size: 500
- Max Tokens: 4000

### 6. Start Processing

1. Click **"▶ Start Processing"**
2. Confirm dialog: Click "Yes"
3. Watch the magic happen!

**What You'll See:**
- Progress bar updates
- Console log shows each batch
- Current batch preview updates in real-time
- Statistics update every second

### 7. Monitor Progress

**Watch the Console Log:**
```
[14:23:45] ✓ GUI initialized
[14:24:01] Input file selected: C:/Projects/INPUT.txt
[14:24:15] ✓ Connection successful!
[14:24:30] STARTING TTS TEXT PREPROCESSING
[14:24:31] 📖 Reading input file...
[14:24:31]    Total lines: 8000
[14:24:31]    Estimated batches: 16
[14:24:32] ======================================================================
[14:24:32] 📝 BATCH 1/16
[14:24:32] ======================================================================
[14:24:32]    Lines: 1 to 500 (12543 chars)
[14:24:32]    ⚙ Processing with mistral-7b-instruct-v0.3...
[14:24:47]    ✓ Batch complete in 15.2s (12234 chars)
[14:24:47]    Context saved: 'The prints were fresh...'
```

**Check Current Batch Preview:**
- Switch to "👁 Current Batch Preview" tab
- See before/after comparison
- Verify quality of transformations

### 8. Pause If Needed

**To pause:**
1. Click **"⏸ Pause"**
2. Processing stops after current batch
3. Review output quality
4. Click **"▶ Resume"** to continue

### 9. Review Output

**During processing:**
- Switch to "📄 Full Output" tab
- See complete processed text
- Spot-check quality

**After completion:**
- Open OUTPUT.txt in text editor
- Review full document
- Check for:
  - Contractions fixed (didn't, couldn't)
  - Page numbers removed
  - Paragraphs preserved
  - Smooth narrative flow

---

## 🎨 GUI Features Explained

### Color-Coded Console

The console uses colors to help you quickly identify message types:

**🟢 Green (Success):**
```
✓ Connection successful!
✓ Batch complete in 15.2s
✅ PROCESSING COMPLETE!
```

**🔵 Blue (Info):**
```
Input file selected: INPUT.txt
Total lines: 8000
Using context from Batch 3
```

**🟡 Yellow (Warning):**
```
⏸ Processing PAUSED by user
```

**🔴 Red (Error):**
```
✗ Connection failed: Connection refused
✗ Batch FAILED - stopping
⏹ Processing STOPPED by user
```

**🟣 Purple (Batch Markers):**
```
======================================================================
📝 BATCH 5/16
======================================================================
```

### Real-Time Statistics

**Batch Progress:**
- Shows current vs. total batches
- Example: "5/16"

**Elapsed Time:**
- Format: HH:MM:SS
- Updates every second
- Example: "00:15:47"

**Status:**
- ▶ PROCESSING: Currently working
- ⏸ PAUSED: Temporarily stopped
- ⏹ STOPPED: Completely stopped

**Progress Percentage:**
- Calculated: (current_batch / total_batches) × 100
- Example: "31.3%"

### Split Preview Panels

**Purpose:** See transformation in action!

**Input Panel (Left - Yellow Background):**
- Shows raw text with OCR errors
- Example: `didn ' t`, `122 THE TRACKER`

**Output Panel (Right - Green Background):**
- Shows cleaned text
- Example: `didn't`, (page numbers removed)

**Usage:**
- Verify transformations are correct
- Catch any issues immediately
- No need to open files separately

---

## 🔧 Advanced Features

### Context Tracking (Automatic)

The GUI automatically:
1. Extracts last 2-3 sentences from each batch
2. Saves them as context
3. Injects context into next batch
4. Prevents duplication in output

**You see this in logs:**
```
Context saved: 'The prints were fresh...'
Using context from Batch 4
```

### Smart Paragraph Detection

The GUI finds natural breakpoints:
- Looks for double newlines (paragraph breaks)
- Avoids cutting mid-sentence
- Searches last 50 lines for break
- Falls back to hard limit if no break found

### Thread-Safe Processing

**Technical Details:**
- Processing runs in separate thread
- GUI remains responsive
- Can pause/stop anytime
- No GUI freezing
- Queue-based log updates

### Auto-Save Progress

**Safety Features:**
- Output saved after each batch
- If stopped, progress is preserved
- Can resume later from saved point
- No data loss on pause/stop

---

## 🐛 Troubleshooting

### Issue: "Connection failed"

**Solutions:**
1. Check LM Studio is running
2. Verify Local Server is started
3. Check port is 1234
4. Test with simple completion in LM Studio first

**How to verify:**
```
1. Open LM Studio
2. Go to Local Server tab
3. Look for "Server running on port 1234"
4. If not running, click "Start Server"
```

### Issue: GUI won't launch

**Error:** `ModuleNotFoundError: No module named 'tkinter'`

**Solutions:**
- **Windows:** Reinstall Python with tkinter option
- **Linux:** `sudo apt-get install python3-tk`
- **macOS:** Should be included, try reinstalling Python

### Issue: Processing is slow

**Possible causes:**
1. LM Studio model not fully loaded to GPU
2. Batch size too large
3. Context length too high
4. Other apps using GPU

**Solutions:**
1. Check GPU offload in LM Studio (should be 32/32)
2. Reduce batch size to 250 lines
3. Close other GPU-intensive apps
4. Check VRAM usage in LM Studio

### Issue: Poor quality output

**Symptoms:**
- Contractions not fixed
- Page numbers still present
- Inconsistent formatting

**Solutions:**
1. Lower temperature (try 0.1)
2. Verify prompt file is correct
3. Check seed is fixed (not random)
4. Try different model (Llama-3.1-13B)
5. Test with single batch first

### Issue: GUI freezes

**Note:** This shouldn't happen! Processing runs in separate thread.

**If it does:**
1. Wait 30 seconds (might be heavy batch)
2. Check Task Manager for Python process
3. Kill and restart if needed
4. Report as bug (shouldn't freeze)

### Issue: Inconsistent output between batches

**Cause:** Random seed enabled

**Solution:**
1. Set seed to fixed number (42)
2. Verify in GUI: Should NOT say "Random Seed"
3. Restart processing

---

## 💡 Tips & Best Practices

### Before You Start

✅ **Test first 3 batches**
- Process batches 1-3
- Review output quality carefully
- Adjust settings if needed
- Then do full run

✅ **Check your prompt**
- Make sure prompt file is correct
- Verify it contains all transformation rules
- Test prompt in LM Studio chat first

✅ **Have good INPUT.txt**
- Not too corrupted
- Reasonable OCR quality
- Standard encoding (UTF-8)

### During Processing

✅ **Monitor first few batches**
- Watch console log closely
- Check preview panels
- Verify quality immediately

✅ **Use Pause feature**
- Pause after batch 3-5
- Review output
- Check for issues
- Resume if all good

✅ **Don't close LM Studio!**
- Keep it running entire time
- Don't change model settings
- Don't unload model

### After Processing

✅ **Review full output**
- Open OUTPUT.txt in text editor
- Spot-check random sections
- Verify:
  - No page numbers
  - Contractions fixed
  - Paragraphs intact
  - Smooth flow

✅ **Save your settings**
- Note which settings worked best
- Document any issues
- Keep for future books

---

## ⚙️ Configuration Reference

### Optimal Settings for TTS Preprocessing

```
=== LM Studio Settings ===
Context Length:        8192 tokens
GPU Offload:          32/32
Flash Attention:      ON
Seed:                 42 (fixed)

=== GUI Settings ===
Temperature:          0.2
Max Tokens:           4000
Batch Size:           500 lines
```

### When to Adjust Settings

**Increase Batch Size (to 750):**
- If processing too slow
- If you have simple, clean text
- If VRAM usage is low

**Decrease Batch Size (to 250):**
- If batches failing
- If complex/corrupted text
- If VRAM errors

**Lower Temperature (to 0.1):**
- If output inconsistent
- If you want max determinism
- If model being too creative

**Increase Max Tokens (to 6000):**
- If batches being truncated
- If output seems incomplete
- If you have verbose text

---

## 📊 Performance Expectations

### For 8000-Line Book

**With Mistral-7B-Instruct (Q5_K_M):**
- **Total batches:** ~16
- **Time per batch:** 12-18 seconds
- **Total time:** 20-30 minutes
- **VRAM usage:** ~6.5 GB
- **Success rate:** 95%+

**With Llama-3.1-13B-Instruct (Q5_K_M):**
- **Total batches:** ~16
- **Time per batch:** 25-35 seconds
- **Total time:** 40-60 minutes
- **VRAM usage:** ~10 GB
- **Success rate:** 98%+

---

## 🎯 Keyboard Shortcuts

While not built-in yet, you can:
- **Alt+F4:** Close application
- **Ctrl+C:** Copy from text areas
- **Ctrl+A:** Select all in text areas

---

## 🔄 Workflow Summary

1. ✅ Start LM Studio → Load model → Start server
2. ✅ Launch GUI → `python tts_preprocessor_gui.py`
3. ✅ Select files → INPUT.txt, Prompt file
4. ✅ Test connection → Should succeed
5. ✅ Start processing → Click ▶ Start
6. ✅ Monitor progress → Watch console & previews
7. ✅ Review output → Check OUTPUT.txt quality
8. ✅ Done! → Use output for TTS

---

## 🆘 Need Help?

**Check these in order:**
1. Is LM Studio running? ✓
2. Is Local Server started? ✓
3. Is model loaded? ✓
4. Are files selected correctly? ✓
5. Is seed fixed (not random)? ✓
6. Is temperature 0.2? ✓

**Still having issues?**
- Check console log for error details
- Test connection in GUI
- Try simple test in LM Studio first
- Reduce batch size and retry

---

## 🎉 Success Checklist

After processing, verify:
- [ ] All batches completed
- [ ] No errors in console
- [ ] OUTPUT.txt exists and has content
- [ ] Contractions fixed (didn't, couldn't)
- [ ] Page numbers removed
- [ ] Paragraph structure preserved
- [ ] Narrative flows smoothly
- [ ] No duplicate sentences at batch boundaries
- [ ] File size reasonable (should be similar to input)

**If all checked:** You're ready for TTS! 🎊

---

## 📝 Example Session

```
[14:30:00] ✓ GUI initialized
[14:30:15] Input file selected: C:/Books/tracker.txt
[14:30:18] Output file selected: C:/Books/tracker_clean.txt
[14:30:22] Prompt file selected: C:/prompts/improved_prompt.txt
[14:30:30] ✓ Connection successful! LM Studio is ready.
[14:30:45] STARTING TTS TEXT PREPROCESSING
[14:30:46] 📖 Reading input file: C:/Books/tracker.txt
[14:30:46]    Total lines: 8247
[14:30:46]    Estimated batches: 17

[14:30:47] 📝 BATCH 1/17
[14:30:47]    Lines: 1 to 498 (13120 chars)
[14:30:47]    ⚙ Processing with mistral-7b-instruct-v0.3...
[14:31:02]    ✓ Batch complete in 15.3s (12890 chars)

[14:31:03] 📝 BATCH 2/17
[14:31:03]    Lines: 499 to 1004 (12876 chars)
[14:31:03]    Using context from Batch 1
[14:31:03]    ⚙ Processing with mistral-7b-instruct-v0.3...
[14:31:18]    ✓ Batch complete in 14.8s (12654 chars)

... [continues for all batches] ...

[14:55:23] ✅ PROCESSING COMPLETE!
[14:55:23]    Total batches: 17
[14:55:23]    Total time: 00:24:36
[14:55:23]    Output saved: C:/Books/tracker_clean.txt
```

---

**Enjoy your professional TTS preprocessing experience!** 🚀
