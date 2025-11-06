"""
TTS Text Preprocessor GUI
A professional interface for batch processing text with LM Studio
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import openai
import re
import time
import json
from pathlib import Path
from datetime import datetime

class TTSPreprocessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Text Preprocessor - LM Studio Edition")
        self.root.geometry("1400x900")
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.prompt_file = tk.StringVar()
        self.lm_host = tk.StringVar(value="http://localhost:1234/v1")
        self.model_name = tk.StringVar(value="mistral-7b-instruct-v0.3")
        self.temperature = tk.DoubleVar(value=0.2)
        self.seed = tk.IntVar(value=42)
        self.batch_size = tk.IntVar(value=500)
        self.max_tokens = tk.IntVar(value=4000)
        
        # Processing state
        self.is_processing = False
        self.is_paused = False
        self.current_batch = 0
        self.total_batches = 0
        self.start_time = None
        self.previous_context = ""
        
        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Build UI
        self.setup_ui()
        
        # Start log queue processor
        self.process_log_queue()
        
    def setup_ui(self):
        """Build the complete UI"""
        
        # ==== TOP SECTION: Configuration ====
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # File Selection
        files_frame = ttk.Frame(config_frame)
        files_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(files_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2, padx=5)
        
        ttk.Label(files_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5)
        
        ttk.Label(files_frame, text="Prompt File:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.prompt_file, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_prompt).grid(row=2, column=2, padx=5)
        
        # LM Studio Settings
        lm_frame = ttk.Frame(config_frame)
        lm_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lm_frame, text="LM Studio Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.lm_host, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(lm_frame, text="Model:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.model_name, width=30).grid(row=0, column=3, padx=5)
        
        ttk.Button(lm_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=4, padx=5)
        
        # Model Parameters
        params_frame = ttk.Frame(config_frame)
        params_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=0.0, to=1.0, increment=0.1, 
                    textvariable=self.temperature, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(params_frame, text="Seed:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=1, to=9999, increment=1, 
                    textvariable=self.seed, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(params_frame, text="Batch Size (lines):").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=100, to=1000, increment=50, 
                    textvariable=self.batch_size, width=10).grid(row=0, column=5, padx=5)
        
        ttk.Label(params_frame, text="Max Tokens:").grid(row=0, column=6, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=1000, to=8000, increment=500, 
                    textvariable=self.max_tokens, width=10).grid(row=0, column=7, padx=5)
        
        # ==== MIDDLE SECTION: Progress & Controls ====
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress Bar
        progress_frame = ttk.LabelFrame(control_frame, text="Progress", padding=10)
        progress_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to process", font=('Arial', 10))
        self.progress_label.pack()
        
        # Statistics
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding=10)
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, width=40, font=('Courier', 9))
        self.stats_text.pack()
        self.update_stats()
        
        # Control Buttons
        button_frame = ttk.LabelFrame(control_frame, text="Controls", padding=10)
        button_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Processing", 
                                    command=self.start_processing, style='Accent.TButton')
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.pause_btn = ttk.Button(button_frame, text="⏸ Pause", 
                                    command=self.pause_processing, state=tk.DISABLED)
        self.pause_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", 
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        # ==== BOTTOM SECTION: Preview & Logs (Tabbed) ====
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
        
        # Tab 2: Current Batch Preview
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="👁 Current Batch Preview")
        
        preview_paned = ttk.PanedWindow(preview_frame, orient=tk.HORIZONTAL)
        preview_paned.pack(fill=tk.BOTH, expand=True)
        
        # Input preview
        input_preview_frame = ttk.LabelFrame(preview_paned, text="Input Text")
        self.input_preview = scrolledtext.ScrolledText(input_preview_frame, wrap=tk.WORD, 
                                                       font=('Arial', 9), bg='#fff8dc')
        self.input_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(input_preview_frame)
        
        # Output preview
        output_preview_frame = ttk.LabelFrame(preview_paned, text="Output Text")
        self.output_preview = scrolledtext.ScrolledText(output_preview_frame, wrap=tk.WORD, 
                                                        font=('Arial', 9), bg='#e8f4ea')
        self.output_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(output_preview_frame)
        
        # Tab 3: Full Output View
        output_frame = ttk.Frame(notebook)
        notebook.add(output_frame, text="📄 Full Output")
        
        self.full_output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                          font=('Arial', 10))
        self.full_output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.log_message("✓ GUI initialized. Configure settings and load files to begin.", 'success')
    
    def browse_input(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            self.log_message(f"Input file selected: {filename}", 'info')
            
            # Auto-suggest output file
            if not self.output_file.get():
                output_path = str(Path(filename).parent / "OUTPUT.txt")
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
    
    def browse_prompt(self):
        """Browse for prompt file"""
        filename = filedialog.askopenfilename(
            title="Select Prompt File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.prompt_file.set(filename)
            self.log_message(f"Prompt file selected: {filename}", 'info')
    
    def test_connection(self):
        """Test connection to LM Studio"""
        self.log_message("Testing connection to LM Studio...", 'info')
        try:
            client = openai.OpenAI(
                base_url=self.lm_host.get(),
                api_key="not-needed"
            )
            
            # Try a simple completion
            response = client.chat.completions.create(
                model=self.model_name.get(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            self.log_message("✓ Connection successful! LM Studio is ready.", 'success')
            messagebox.showinfo("Connection Test", "✓ Successfully connected to LM Studio!")
            
        except Exception as e:
            self.log_message(f"✗ Connection failed: {str(e)}", 'error')
            messagebox.showerror("Connection Test", f"Failed to connect:\n{str(e)}\n\nMake sure LM Studio Local Server is running!")
    
    def log_message(self, message, tag='info'):
        """Add message to log (thread-safe via queue)"""
        self.log_queue.put((message, tag))
    
    def process_log_queue(self):
        """Process queued log messages"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
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
            
            stats = f"""Batch:     {self.current_batch}/{self.total_batches}
Time:      {elapsed_str}
Status:    {'⏸ PAUSED' if self.is_paused else '▶ PROCESSING'}
Progress:  {self.progress_bar['value']:.1f}%"""
        else:
            stats = """Batch:     -
Time:      00:00:00
Status:    ⏹ STOPPED
Progress:  0.0%"""
        
        self.stats_text.insert(1.0, stats)
        
        if self.is_processing:
            self.root.after(1000, self.update_stats)
    
    def start_processing(self):
        """Start the batch processing"""
        # Validation
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file!")
            return
        
        if not self.output_file.get():
            messagebox.showerror("Error", "Please select an output file!")
            return
        
        if not self.prompt_file.get():
            messagebox.showerror("Error", "Please select a prompt file!")
            return
        
        # Confirm start
        if not messagebox.askyesno("Start Processing", 
                                   f"Start processing {self.input_file.get()}?\n\nThis will overwrite {self.output_file.get()}"):
            return
        
        # Update UI
        self.is_processing = True
        self.is_paused = False
        self.current_batch = 0
        self.start_time = time.time()
        self.previous_context = ""
        
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Clear output file
        with open(self.output_file.get(), 'w', encoding='utf-8') as f:
            f.write('')
        
        self.log_message("="*70, 'info')
        self.log_message("STARTING TTS TEXT PREPROCESSING", 'batch')
        self.log_message("="*70, 'info')
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_batches, daemon=True)
        thread.start()
        
        self.update_stats()
    
    def pause_processing(self):
        """Pause/Resume processing"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.config(text="▶ Resume")
            self.log_message("⏸ Processing PAUSED by user", 'warning')
        else:
            self.pause_btn.config(text="⏸ Pause")
            self.log_message("▶ Processing RESUMED", 'success')
        
        self.update_stats()
    
    def stop_processing(self):
        """Stop processing"""
        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop?\n\nProgress will be saved."):
            self.is_processing = False
            self.log_message("⏹ Processing STOPPED by user", 'error')
            self.finish_processing()
    
    def finish_processing(self):
        """Clean up after processing"""
        self.is_processing = False
        self.is_paused = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.progress_bar['value'] = 0
        self.update_stats()
    
    def extract_last_sentences(self, text, num_sentences=3):
        """Extract last N sentences for context"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        last_sentences = sentences[-num_sentences:] if len(sentences) >= num_sentences else sentences
        return ' '.join(last_sentences) + '.' if last_sentences else ""
    
    def find_paragraph_break(self, lines, max_lookback=50):
        """Find natural paragraph break"""
        for i in range(len(lines)-1, max(len(lines)-max_lookback, 0), -1):
            if i > 0 and lines[i].strip() == '':
                return i
        return len(lines)
    
    def process_single_batch(self, text_batch, batch_num, context=""):
        """Process a single batch with LM Studio"""
        try:
            # Build user message
            if context and batch_num > 1:
                user_message = f"""CONTEXT FROM PREVIOUS BATCH (for reference only - DO NOT output):
"{context}"

NOW PROCESS THIS NEW TEXT:
{text_batch}

Remember: Only output the cleaned NEW text, not the context."""
            else:
                user_message = text_batch
            
            # Load system prompt
            with open(self.prompt_file.get(), 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            
            # Create client
            client = openai.OpenAI(
                base_url=self.lm_host.get(),
                api_key="not-needed"
            )
            
            # Make request
            response = client.chat.completions.create(
                model=self.model_name.get(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature.get(),
                max_tokens=self.max_tokens.get(),
                seed=self.seed.get()
            )
            
            cleaned_text = response.choices[0].message.content
            next_context = self.extract_last_sentences(cleaned_text, 3)
            
            return cleaned_text, next_context
            
        except Exception as e:
            self.log_message(f"✗ Error processing batch {batch_num}: {str(e)}", 'error')
            return None, context
    
    def process_batches(self):
        """Main processing loop (runs in separate thread)"""
        try:
            # Read input file
            self.log_message(f"📖 Reading input file: {self.input_file.get()}", 'info')
            with open(self.input_file.get(), 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            self.log_message(f"   Total lines: {total_lines}", 'info')
            
            # Calculate total batches
            self.total_batches = (total_lines // self.batch_size.get()) + 1
            self.log_message(f"   Estimated batches: {self.total_batches}", 'info')
            
            batch_size = self.batch_size.get()
            i = 0
            batch_num = 1
            
            while i < total_lines and self.is_processing:
                # Wait if paused
                while self.is_paused and self.is_processing:
                    time.sleep(0.5)
                
                if not self.is_processing:
                    break
                
                # Determine batch end
                batch_end = min(i + batch_size, total_lines)
                batch_lines = lines[i:batch_end]
                
                # Find natural breakpoint
                if batch_end < total_lines:
                    break_point = self.find_paragraph_break(batch_lines)
                    batch_lines = batch_lines[:break_point]
                    actual_end = i + break_point
                else:
                    actual_end = batch_end
                
                batch_text = ''.join(batch_lines)
                
                # Update preview
                self.input_preview.delete(1.0, tk.END)
                self.input_preview.insert(1.0, batch_text[:2000] + "..." if len(batch_text) > 2000 else batch_text)
                
                # Log batch info
                self.log_message(f"\n{'='*70}", 'batch')
                self.log_message(f"📝 BATCH {batch_num}/{self.total_batches}", 'batch')
                self.log_message(f"{'='*70}", 'batch')
                self.log_message(f"   Lines: {i+1} to {actual_end} ({len(batch_text)} chars)", 'info')
                
                if self.previous_context:
                    self.log_message(f"   Using context from Batch {batch_num-1}", 'info')
                
                # Process batch
                self.log_message(f"   ⚙ Processing with {self.model_name.get()}...", 'info')
                batch_start_time = time.time()
                
                cleaned, next_context = self.process_single_batch(
                    batch_text, 
                    batch_num, 
                    self.previous_context
                )
                
                batch_time = time.time() - batch_start_time
                
                if cleaned:
                    # Update output preview
                    self.output_preview.delete(1.0, tk.END)
                    self.output_preview.insert(1.0, cleaned[:2000] + "..." if len(cleaned) > 2000 else cleaned)
                    
                    # Append to output file
                    with open(self.output_file.get(), 'a', encoding='utf-8') as f:
                        f.write(cleaned)
                        if not cleaned.endswith('\n\n'):
                            f.write('\n\n')
                    
                    # Update full output view
                    self.full_output_text.insert(tk.END, cleaned + '\n\n')
                    self.full_output_text.see(tk.END)
                    
                    # Save context
                    self.previous_context = next_context
                    
                    self.log_message(f"   ✓ Batch complete in {batch_time:.1f}s ({len(cleaned)} chars)", 'success')
                    self.log_message(f"   Context saved: '{next_context[:60]}...'", 'info')
                else:
                    self.log_message(f"   ✗ Batch FAILED - stopping", 'error')
                    break
                
                # Update progress
                self.current_batch = batch_num
                progress = (batch_num / self.total_batches) * 100
                self.progress_bar['value'] = progress
                self.progress_label.config(text=f"Batch {batch_num}/{self.total_batches} complete ({progress:.1f}%)")
                
                # Move to next batch
                i = actual_end
                batch_num += 1
            
            # Processing complete
            if self.is_processing:
                elapsed = time.time() - self.start_time
                self.log_message(f"\n{'='*70}", 'success')
                self.log_message(f"✅ PROCESSING COMPLETE!", 'success')
                self.log_message(f"{'='*70}", 'success')
                self.log_message(f"   Total batches: {batch_num-1}", 'success')
                self.log_message(f"   Total time: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}", 'success')
                self.log_message(f"   Output saved: {self.output_file.get()}", 'success')
                
                messagebox.showinfo("Complete", f"Processing complete!\n\nBatches processed: {batch_num-1}\nOutput saved to: {self.output_file.get()}")
            
        except Exception as e:
            self.log_message(f"\n✗ FATAL ERROR: {str(e)}", 'error')
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")
        
        finally:
            self.finish_processing()


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    style.theme_use('clam')
    
    # Custom button style
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = TTSPreprocessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
