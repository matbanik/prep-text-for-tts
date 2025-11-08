#!/usr/bin/env python3
"""
OCR GUI Application
Standalone GUI for PDF to Text extraction using various OCR models
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
from pathlib import Path
from datetime import datetime
import time

from ocr_processor import OCRProcessor, DEFAULT_OCR_MODEL


class OCRProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Processor - PDF to Text Extraction")
        self.root.geometry("1200x800")

        # Variables
        self.pdf_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.lm_studio_host = tk.StringVar(value="http://localhost:1234/v1")
        self.model_name = tk.StringVar(value=DEFAULT_OCR_MODEL)
        self.dpi = tk.IntVar(value=300)
        self.apply_cleanup = tk.BooleanVar(value=True)
        self.chunk_for_tts = tk.BooleanVar(value=True)

        # Processing state
        self.is_processing = False
        self.connected = False
        self.processor = None
        self.start_time = None

        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()

        # Build UI
        self.setup_ui()

        # Start log queue processor
        self.process_log_queue()

        # Check dependencies on startup
        self.root.after(500, self.check_dependencies)

    def setup_ui(self):
        """Build the complete UI"""

        # ==== TOP SECTION: Configuration ====
        config_frame = ttk.LabelFrame(self.root, text="OCR Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # File Selection
        files_frame = ttk.Frame(config_frame)
        files_frame.pack(fill=tk.X, pady=5)

        ttk.Label(files_frame, text="PDF File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.pdf_file, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_pdf).grid(row=0, column=2, padx=5)

        ttk.Label(files_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.output_file, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5)

        # LM Studio Settings
        lm_frame = ttk.LabelFrame(config_frame, text="LM Studio Settings", padding=5)
        lm_frame.pack(fill=tk.X, pady=10)

        ttk.Label(lm_frame, text="LM Studio Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.lm_studio_host, width=40).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(lm_frame, text="Model Name:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.model_name, width=40).grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(lm_frame, text="ℹ Load Qwen2-VL-7B-Instruct in LM Studio before connecting",
                 foreground='blue').grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="DPI:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Spinbox(options_frame, from_=150, to=600, increment=50,
                    textvariable=self.dpi, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(options_frame, text="(Image quality - higher = better but slower)").grid(row=0, column=2, sticky=tk.W, padx=5)

        ttk.Checkbutton(options_frame, text="Apply post-processing cleanup",
                       variable=self.apply_cleanup).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        ttk.Checkbutton(options_frame, text="Chunk for TTS (250 chars per line)",
                       variable=self.chunk_for_tts).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # ==== MIDDLE SECTION: Control Buttons ====
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        button_frame = ttk.LabelFrame(control_frame, text="Controls", padding=10)
        button_frame.pack(side=tk.LEFT, padx=5)

        self.check_deps_btn = ttk.Button(button_frame, text="🔍 Check Dependencies",
                                         command=self.check_dependencies)
        self.check_deps_btn.pack(fill=tk.X, pady=2)

        self.connect_btn = ttk.Button(button_frame, text="🔌 Connect to LM Studio",
                                      command=self.connect_lm_studio)
        self.connect_btn.pack(fill=tk.X, pady=2)

        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(button_frame, text="▶ Start OCR Processing",
                                    command=self.start_processing, style='Accent.TButton')
        self.start_btn.pack(fill=tk.X, pady=2)
        self.start_btn.config(state=tk.DISABLED)

        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop",
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)

        # Progress
        progress_frame = ttk.LabelFrame(control_frame, text="Progress", padding=10)
        progress_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="Ready", font=('Arial', 10))
        self.progress_label.pack()

        # Statistics
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding=10)
        stats_frame.pack(side=tk.LEFT, padx=5)

        self.stats_text = tk.Text(stats_frame, height=6, width=35, font=('Courier', 9))
        self.stats_text.pack()
        self.update_stats()

        # ==== BOTTOM SECTION: Logs & Preview (Tabbed) ====
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Console Log
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="📋 Console Log")

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                   font=('Courier', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure log text tags for colors
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4fc1ff')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('batch', foreground='#c586c0')

        # Tab 2: Output Preview
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="👁 Output Preview")

        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD,
                                                      font=('Arial', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready to process PDFs", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.log_message("✓ OCR GUI initialized. Select a PDF file and connect to LM Studio to begin.", 'success')

    def browse_pdf(self):
        """Browse for PDF file"""
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_file.set(filename)
            self.log_message(f"PDF file selected: {filename}", 'info')

            # Auto-suggest output file
            if not self.output_file.get():
                output_path = str(Path(filename).parent / f"{Path(filename).stem}_OCR.txt")
                self.output_file.set(output_path)

    def browse_output(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            self.log_message(f"Output file selected: {filename}", 'info')


    def check_dependencies(self):
        """Check if required dependencies are installed"""
        self.log_message("="*70, 'info')
        self.log_message("Checking dependencies...", 'info')

        missing = OCRProcessor.check_dependencies()

        if missing:
            self.log_message(f"✗ Missing dependencies: {', '.join(missing)}", 'error')
            self.log_message(f"Install with: pip install {' '.join(missing)}", 'warning')
            messagebox.showerror("Missing Dependencies",
                               f"Missing packages:\n\n{chr(10).join(missing)}\n\n"
                               f"Install with:\npip install {' '.join(missing)}")
        else:
            self.log_message("✓ All dependencies installed!", 'success')
            messagebox.showinfo("Dependencies OK", "✓ All required packages are installed!")

    def connect_lm_studio(self):
        """Connect to LM Studio"""
        if self.connected:
            if not messagebox.askyesno("Already Connected",
                                      "Already connected to LM Studio. Reconnect?"):
                return

        # Check dependencies first
        missing = OCRProcessor.check_dependencies()
        if missing:
            messagebox.showerror("Missing Dependencies",
                               f"Cannot connect. Missing:\n{', '.join(missing)}\n\n"
                               f"Install with: pip install {' '.join(missing)}")
            return

        self.log_message("="*70, 'batch')
        self.log_message(f"Connecting to LM Studio...", 'batch')
        self.log_message("="*70, 'batch')

        # Disable buttons during connection
        self.connect_btn.config(state=tk.DISABLED)
        self.check_deps_btn.config(state=tk.DISABLED)

        # Start connection in thread
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()

    def _connect_thread(self):
        """Connect to LM Studio in background thread"""
        try:
            self.processor = OCRProcessor(
                lm_studio_host=self.lm_studio_host.get(),
                model_name=self.model_name.get()
            )

            def progress_callback(msg):
                self.log_queue.put((msg, 'info'))

            self.processor.connect(progress_callback=progress_callback)

            self.connected = True
            self.log_queue.put(("✓ Connected to LM Studio successfully! Ready to process PDFs.", 'success'))

            # Enable start button
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: messagebox.showinfo("Connected",
                                                          f"✓ Connected to LM Studio!\n\n"
                                                          f"Model: {self.model_name.get()}\n\n"
                                                          f"You can now process PDF files."))

        except Exception as e:
            self.log_queue.put((f"✗ Connection failed: {str(e)}", 'error'))
            self.root.after(0, lambda: messagebox.showerror("Connection Failed",
                                                           f"Failed to connect to LM Studio:\n\n{str(e)}\n\n"
                                                           f"Make sure:\n"
                                                           f"1. LM Studio is running\n"
                                                           f"2. Local Server is started\n"
                                                           f"3. Qwen2-VL-7B-Instruct is loaded"))

        finally:
            self.root.after(0, lambda: self.connect_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.check_deps_btn.config(state=tk.NORMAL))

    def start_processing(self):
        """Start OCR processing"""
        # Validation
        if not self.pdf_file.get():
            messagebox.showerror("Error", "Please select a PDF file!")
            return

        if not self.output_file.get():
            messagebox.showerror("Error", "Please select an output file!")
            return

        if not self.connected:
            messagebox.showerror("Error", "Please connect to LM Studio first!")
            return

        # Confirm start
        if not messagebox.askyesno("Start OCR Processing",
                                   f"Process PDF:\n{self.pdf_file.get()}\n\n"
                                   f"Model: {self.model_name.get()}\n"
                                   f"DPI: {self.dpi.get()}\n\n"
                                   f"This will overwrite:\n{self.output_file.get()}"):
            return

        # Update UI
        self.is_processing = True
        self.start_time = time.time()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.connect_btn.config(state=tk.DISABLED)

        self.log_message("="*70, 'batch')
        self.log_message("STARTING OCR PROCESSING", 'batch')
        self.log_message("="*70, 'batch')

        # Start processing in thread
        thread = threading.Thread(target=self._process_pdf_thread, daemon=True)
        thread.start()

        self.update_stats()

    def _process_pdf_thread(self):
        """Process PDF in background thread"""
        try:
            def progress_callback(msg):
                self.log_queue.put((msg, 'info'))

                # Update progress bar if page info
                if "page" in msg.lower() and "/" in msg:
                    try:
                        # Extract "page X/Y"
                        import re
                        match = re.search(r'(\d+)/(\d+)', msg)
                        if match:
                            current, total = int(match.group(1)), int(match.group(2))
                            progress = (current / total) * 100
                            self.root.after(0, lambda: self.progress_bar.config(value=progress))
                            self.root.after(0, lambda: self.progress_label.config(
                                text=f"Processing page {current}/{total} ({progress:.1f}%)"))
                    except:
                        pass

            # Process PDF
            extracted_text = self.processor.process_pdf(
                self.pdf_file.get(),
                progress_callback=progress_callback
            )

            if not self.is_processing:
                self.log_queue.put(("Processing stopped by user.", 'warning'))
                return

            # Apply post-processing if requested
            if self.apply_cleanup.get() or self.chunk_for_tts.get():
                self.log_queue.put(("", 'info'))
                self.log_queue.put(("Applying post-processing...", 'info'))

                from tts_preprocessor_gui import TextPreprocessor

                if self.chunk_for_tts.get():
                    extracted_text = TextPreprocessor.preprocess_text(extracted_text, max_chunk_size=250)
                    self.log_queue.put(("✓ Text cleaned and chunked for TTS (250 chars/line)", 'success'))
                elif self.apply_cleanup.get():
                    # Apply cleanup without chunking
                    extracted_text = TextPreprocessor.remove_page_numbers(extracted_text)
                    extracted_text = TextPreprocessor.fix_contractions(extracted_text)
                    extracted_text = TextPreprocessor.fix_hyphenated_breaks(extracted_text)
                    extracted_text = TextPreprocessor.expand_abbreviations(extracted_text)
                    extracted_text = TextPreprocessor.remove_unicode_artifacts(extracted_text)
                    extracted_text = TextPreprocessor.normalize_whitespace(extracted_text)
                    self.log_queue.put(("✓ Text cleaned up", 'success'))

            # Save output
            self.log_queue.put(("", 'info'))
            self.log_queue.put((f"Saving to {self.output_file.get()}...", 'info'))

            with open(self.output_file.get(), 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            # Statistics
            char_count = len(extracted_text)
            line_count = extracted_text.count('\n') + 1
            word_count = len(extracted_text.split())

            self.log_queue.put(("✓ File saved successfully!", 'success'))
            self.log_queue.put(("", 'info'))
            self.log_queue.put((f"Statistics:", 'info'))
            self.log_queue.put((f"  Characters: {char_count:,}", 'info'))
            self.log_queue.put((f"  Lines: {line_count:,}", 'info'))
            self.log_queue.put((f"  Words: {word_count:,}", 'info'))

            # Update preview
            preview = extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else "")
            self.root.after(0, lambda: self.preview_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.preview_text.insert(1.0, preview))

            # Show completion
            elapsed = time.time() - self.start_time if self.start_time else 0
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))

            self.log_queue.put(("", 'success'))
            self.log_queue.put(("="*70, 'success'))
            self.log_queue.put(("✅ OCR PROCESSING COMPLETE!", 'success'))
            self.log_queue.put(("="*70, 'success'))
            self.log_queue.put((f"  Total time: {elapsed_str}", 'success'))
            self.log_queue.put((f"  Output: {self.output_file.get()}", 'success'))

            self.root.after(0, lambda: messagebox.showinfo("OCR Complete",
                                                          f"✅ OCR processing complete!\n\n"
                                                          f"Characters: {char_count:,}\n"
                                                          f"Lines: {line_count:,}\n"
                                                          f"Words: {word_count:,}\n\n"
                                                          f"Time: {elapsed_str}\n\n"
                                                          f"Saved to:\n{self.output_file.get()}"))

        except Exception as e:
            self.log_queue.put(("", 'error'))
            self.log_queue.put((f"✗ OCR PROCESSING FAILED: {str(e)}", 'error'))
            import traceback
            self.log_queue.put((traceback.format_exc(), 'error'))

            self.root.after(0, lambda: messagebox.showerror("OCR Failed",
                                                           f"Processing failed:\n\n{str(e)}"))

        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.finish_processing())

    def stop_processing(self):
        """Stop processing"""
        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop?"):
            self.is_processing = False
            self.log_message("⏹ Processing STOPPED by user", 'error')

    def finish_processing(self):
        """Clean up after processing"""
        self.is_processing = False

        self.start_btn.config(state=tk.NORMAL if self.connected else tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.NORMAL)

        self.progress_bar['value'] = 0
        self.progress_label.config(text="Ready")
        self.update_stats()

    def log_message(self, message, tag='info'):
        """Add message to log (thread-safe via queue)"""
        self.log_queue.put((message, tag))

    def process_log_queue(self):
        """Process queued log messages"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")

                if message:  # Only add timestamp for non-empty messages
                    self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                else:
                    self.log_text.insert(tk.END, "\n", tag)

                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_log_queue)

    def update_stats(self):
        """Update statistics display"""
        self.stats_text.delete(1.0, tk.END)

        if self.is_processing:
            elapsed = time.time() - self.start_time if self.start_time else 0
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))

            stats = f"""Model:   {self.model_name.get()[:30]}
Status:  ▶ PROCESSING
Time:    {elapsed_str}
DPI:     {self.dpi.get()}"""
        else:
            connection_status = "✓ Connected" if self.connected else "Not connected"
            stats = f"""Model:   {self.model_name.get()[:30]}
Status:  {connection_status}
Time:    00:00:00
DPI:     {self.dpi.get()}"""

        self.stats_text.insert(1.0, stats)

        if self.is_processing:
            self.root.after(1000, self.update_stats)


def main():
    """Main entry point"""
    root = tk.Tk()

    # Set theme
    style = ttk.Style()
    style.theme_use('clam')

    # Custom button style
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))

    app = OCRProcessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
