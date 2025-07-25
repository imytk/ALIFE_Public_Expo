import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import csv
from datetime import datetime
from PIL import Image, ImageTk
import random

class LivingNonLivingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Living vs Non-Living Classification")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Data storage
        self.user_responses = []
        self.current_item = 0
        self.user_id = None
        self.start_time = None
        
        # Sample data - replace with your actual images/videos
        self.items = [
            {"file": "dog.jpg", "type": "image", "name": "Dog"},
            {"file": "yeast.jpg", "type": "image", "name": "Yeast"},
            {"file": "thermostat.jpg", "type": "image", "name": "Thermostat"},
            {"file": "tornado.mp4", "type": "video", "name": "Tornado"},
            {"file": "fire.jpg", "type": "image", "name": "Fire"},
            {"file": "tree.jpg", "type": "image", "name": "Tree"},
            {"file": "car.jpg", "type": "image", "name": "Car"},
            {"file": "bacteria.jpg", "type": "image", "name": "Bacteria"},
            {"file": "robot.jpg", "type": "image", "name": "Robot"},
            {"file": "flower.jpg", "type": "image", "name": "Flower"},
            {"file": "clock.jpg", "type": "image", "name": "Clock"},
            {"file": "fish.jpg", "type": "image", "name": "Fish"},
            {"file": "volcano.jpg", "type": "image", "name": "Volcano"},
            {"file": "mushroom.jpg", "type": "image", "name": "Mushroom"},
            {"file": "computer.jpg", "type": "image", "name": "Computer"},
            {"file": "bird.jpg", "type": "image", "name": "Bird"},
            {"file": "river.jpg", "type": "image", "name": "River"},
            {"file": "coral.jpg", "type": "image", "name": "Coral"},
            {"file": "mountain.jpg", "type": "image", "name": "Mountain"},
            {"file": "virus.jpg", "type": "image", "name": "Virus"}
        ]
        
        # Shuffle items for random order
        random.shuffle(self.items)
        
        # Initialize GUI
        self.setup_splash_screen()
    
    def setup_splash_screen(self):
        """Create the initial splash screen"""
        self.clear_screen()
        
        # Main frame
        splash_frame = tk.Frame(self.root, bg='#f0f0f0')
        splash_frame.pack(expand=True, fill='both')
        
        # Title
        title_label = tk.Label(
            splash_frame,
            text="Living vs Non-Living\nClassification Exercise",
            font=('Arial', 28, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=50)
        
        # Instructions
        instructions = """
        You will be shown 20 different systems.
        
        For each one, decide whether you think it is:
        • LIVING - has characteristics of life
        • NON-LIVING - does not have characteristics of life
        
        Click your choice and proceed through all 20 items.
        Your responses will be saved at the end.
        """
        
        instruction_label = tk.Label(
            splash_frame,
            text=instructions,
            font=('Arial', 14),
            bg='#f0f0f0',
            fg='#34495e',
            justify='center'
        )
        instruction_label.pack(pady=30)
        
        # Experience level dropdown
        experience_frame = tk.Frame(splash_frame, bg='#f0f0f0')
        experience_frame.pack(pady=20)
        
        tk.Label(
            experience_frame,
            text="What is your experience with ALIFE?",
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        ).pack(pady=(0, 10))
        
        self.experience_var = tk.StringVar()
        self.experience_dropdown = ttk.Combobox(
            experience_frame,
            textvariable=self.experience_var,
            font=('Arial', 11),
            width=35,
            state='readonly'
        )
        
        # Experience options
        experience_options = [
            "Select your experience level...",
            "General public (no specific background)",
            "Undergraduate student in related field",
            "Graduate student in related field", 
            "ALIFE researcher/professional",
            "Biology/Life sciences background",
            "Computer science/AI background",
            "Philosophy/Cognitive science background",
            "Other scientific background"
        ]
        
        self.experience_dropdown['values'] = experience_options
        self.experience_dropdown.set(experience_options[0])  # Default selection
        self.experience_dropdown.pack()
        
        # Start button
        start_button = tk.Button(
            splash_frame,
            text="Start Exercise",
            font=('Arial', 16, 'bold'),
            bg='#3498db',
            fg='white',
            padx=40,
            pady=15,
            command=self.start_exercise,
            cursor='hand2'
        )
        start_button.pack(pady=40)
    
    def start_exercise(self):
        """Initialize the exercise"""
        # Validate experience selection
        if self.experience_var.get() == "Select your experience level...":
            messagebox.showwarning("Selection Required", "Please select your experience level with ALIFE.")
            return
        
        self.experience_level = self.experience_var.get()
        self.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.current_item = 0
        self.user_responses = []
        self.show_classification_screen()
    
    def show_classification_screen(self):
        """Display the main classification interface"""
        self.clear_screen()
        
        # Progress frame
        progress_frame = tk.Frame(self.root, bg='#f0f0f0')
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        progress_text = f"Item {self.current_item + 1} of {len(self.items)}"
        tk.Label(
            progress_frame,
            text=progress_text,
            font=('Arial', 14),
            bg='#f0f0f0'
        ).pack(side='left')
        
        # Progress bar
        progress = tk.Frame(progress_frame, bg='#ecf0f1', height=10)
        progress.pack(side='right', fill='x', expand=True, padx=(20, 0))
        
        progress_fill = tk.Frame(progress, bg='#3498db', height=10)
        fill_width = (self.current_item / len(self.items))
        progress_fill.place(relwidth=fill_width, relheight=1)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Item name
        item_name = self.items[self.current_item]['name']
        name_label = tk.Label(
            content_frame,
            text=item_name,
            font=('Arial', 24, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        name_label.pack(pady=20)
        
        # Image/Video display area
        media_frame = tk.Frame(content_frame, bg='#ffffff', relief='solid', bd=2)
        media_frame.pack(pady=20)
        
        # Placeholder for media (you'll need to implement actual image/video loading)
        media_label = tk.Label(
            media_frame,
            text=f"[{item_name} Image/Video Here]",
            font=('Arial', 16),
            bg='#ffffff',
            fg='#7f8c8d',
            width=40,
            height=15
        )
        media_label.pack(padx=20, pady=20)
        
        # Note about media files
        note_label = tk.Label(
            content_frame,
            text="Note: Place your media files in the same directory as this script",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#95a5a6'
        )
        note_label.pack()
        
        # Classification buttons
        button_frame = tk.Frame(content_frame, bg='#f0f0f0')
        button_frame.pack(pady=40)
        
        living_button = tk.Button(
            button_frame,
            text="LIVING",
            font=('Arial', 18, 'bold'),
            bg='#27ae60',
            fg='white',
            padx=50,
            pady=20,
            command=lambda: self.record_response('living'),
            cursor='hand2'
        )
        living_button.pack(side='left', padx=20)
        
        nonliving_button = tk.Button(
            button_frame,
            text="NON-LIVING",
            font=('Arial', 18, 'bold'),
            bg='#e74c3c',
            fg='white',
            padx=50,
            pady=20,
            command=lambda: self.record_response('non-living'),
            cursor='hand2'
        )
        nonliving_button.pack(side='right', padx=20)
    
    def record_response(self, classification):
        """Record user's classification and move to next item"""
        response_time = datetime.now()
        
        response_data = {
            'item_number': self.current_item + 1,
            'item_name': self.items[self.current_item]['name'],
            'item_file': self.items[self.current_item]['file'],
            'classification': classification,
            'timestamp': response_time.isoformat(),
            'response_time_seconds': (response_time - self.start_time).total_seconds()
        }
        
        self.user_responses.append(response_data)
        
        # Move to next item or finish
        self.current_item += 1
        
        if self.current_item < len(self.items):
            self.show_classification_screen()
        else:
            self.show_completion_screen()
    
    def show_completion_screen(self):
        """Display completion screen and save data"""
        self.clear_screen()
        
        completion_frame = tk.Frame(self.root, bg='#f0f0f0')
        completion_frame.pack(expand=True, fill='both')
        
        # Completion message
        completion_label = tk.Label(
            completion_frame,
            text="Exercise Complete!",
            font=('Arial', 28, 'bold'),
            bg='#f0f0f0',
            fg='#27ae60'
        )
        completion_label.pack(pady=50)
        
        # Summary
        living_count = sum(1 for r in self.user_responses if r['classification'] == 'living')
        nonliving_count = len(self.user_responses) - living_count
        
        summary_text = f"""
        Summary of your classifications:
        
        Living: {living_count} items
        Non-Living: {nonliving_count} items
        Total Time: {(datetime.now() - self.start_time).total_seconds():.1f} seconds
        """
        
        summary_label = tk.Label(
            completion_frame,
            text=summary_text,
            font=('Arial', 14),
            bg='#f0f0f0',
            fg='#34495e',
            justify='center'
        )
        summary_label.pack(pady=30)
        
        # Save data
        self.save_data()
        
        # Buttons
        button_frame = tk.Frame(completion_frame, bg='#f0f0f0')
        button_frame.pack(pady=40)
        
        restart_button = tk.Button(
            button_frame,
            text="Start New Session",
            font=('Arial', 14),
            bg='#3498db',
            fg='white',
            padx=30,
            pady=10,
            command=self.setup_splash_screen,
            cursor='hand2'
        )
        restart_button.pack(side='left', padx=10)
        
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            font=('Arial', 14),
            bg='#95a5a6',
            fg='white',
            padx=30,
            pady=10,
            command=self.root.quit,
            cursor='hand2'
        )
        exit_button.pack(side='right', padx=10)
    
    def save_data(self):
        """Save user responses to files"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Prepare session data
            session_data = {
                'user_id': self.user_id,
                'experience_level': self.experience_level,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_items': len(self.items),
                'responses': self.user_responses
            }
            
            # Save as JSON
            json_filename = f"data/session_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Save as CSV (flat format)
            csv_filename = f"data/responses_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['user_id', 'experience_level', 'item_number', 'item_name', 'item_file', 'classification', 'timestamp', 'response_time_seconds'])
                
                for response in self.user_responses:
                    writer.writerow([
                        self.user_id,
                        self.experience_level,
                        response['item_number'],
                        response['item_name'],
                        response['item_file'],
                        response['classification'],
                        response['timestamp'],
                        response['response_time_seconds']
                    ])
            
            messagebox.showinfo("Data Saved", f"Your responses have been saved to:\n{json_filename}\n{csv_filename}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving data: {str(e)}")
    
    def clear_screen(self):
        """Clear all widgets from the screen"""
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = LivingNonLivingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()