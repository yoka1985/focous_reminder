import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
import threading
import time
import os
import csv
import datetime
import pygame
from functools import partial

class FocusReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Reminder")
        
        # Set window position to bottom-left corner
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.1)
        window_height = int(screen_height * 0.07)
        self.root.geometry(f"{window_width}x{window_height}+0+{screen_height - window_height}")
        
        # App state variables
        self.paused = False
        self.expanded = False
        self.playing_concentration = False
        self.pomodoro_count = 0
        self.current_interval = 0  # 0, 1, 2 for work intervals, 3 for break
        self.total_pomodoros_completed = 0
        self.original_pomodoro_time = 0
        self.pomodoro_time = 0
        self.break_time = 0
        self.time_remaining = 0
        self.daily_intention = ""
        self.goals = []
        self.completed_goals = []
        self.running = False
        self.timer_thread = None
        self.sound_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
        
        # Initialize pygame mixer for sounds
        pygame.mixer.init()
        
        # Main frame for the compact view
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Timer label and controls
        self.timer_label = ttk.Label(self.main_frame, text="00:00", font=("Arial", 20))
        self.timer_label.pack(pady=5)
        
        # Control buttons frame
        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X)
        
        # Buttons
        self.start_pause_button = ttk.Button(self.controls_frame, text="Start", command=self.toggle_pause)
        self.start_pause_button.pack(side=tk.LEFT, padx=2)
        
        self.concentration_button = ttk.Button(self.controls_frame, text="🔊", command=self.toggle_concentration)
        self.concentration_button.pack(side=tk.LEFT, padx=2)
        
        self.gedit_button = ttk.Button(self.controls_frame, text="📝", command=self.open_gedit)
        self.gedit_button.pack(side=tk.LEFT, padx=2)
        
        self.expand_button = ttk.Button(self.controls_frame, text="⬇️", command=self.toggle_expand)
        self.expand_button.pack(side=tk.LEFT, padx=2)
        
        self.minimize_button = ttk.Button(self.controls_frame, text="—", command=self.minimize_app)
        self.minimize_button.pack(side=tk.LEFT, padx=2)
        
        # Expanded view frame (hidden initially)
        self.expanded_frame = ttk.Frame(root)
        
        # Show setup wizard to collect daily intention and goals
        self.root.after(100, self.show_setup_wizard)
    
    def show_setup_wizard(self):
        # Create wizard window
        wizard = tk.Toplevel(self.root)
        wizard.title("Daily Setup")
        wizard.geometry("400x450")
        wizard.transient(self.root)
        wizard.grab_set()
        
        # Daily intention
        ttk.Label(wizard, text="Your daily intention (max 28 chars):", font=("Arial", 12)).pack(pady=(20, 5))
        intention_entry = ttk.Entry(wizard, width=30)
        intention_entry.pack(pady=5)
        intention_entry.bind("<Return>", lambda e: goals_frame.focus_set())
        
        # Goals
        ttk.Label(wizard, text="Three goals for today (max 28 chars each):", font=("Arial", 12)).pack(pady=(15, 5))
        goals_frame = ttk.Frame(wizard)
        goals_frame.pack(pady=10)
        
        goal_entries = []
        for i in range(3):
            entry = ttk.Entry(goals_frame, width=30)
            entry.pack(pady=5)
            goal_entries.append(entry)
            if i < 2:
                entry.bind("<Return>", lambda e, idx=i: goal_entries[idx+1].focus_set())
            else:
                entry.bind("<Return>", lambda e: time_entry.focus_set())
        
        # Pomodoro time
        ttk.Label(wizard, text="Set Pomodoro cycle time (minutes):", font=("Arial", 12)).pack(pady=(15, 5))
        time_entry = ttk.Entry(wizard, width=10)
        time_entry.pack(pady=5)
        time_entry.insert(0, "25")
        time_entry.bind("<Return>", lambda e: confirm_setup())
        
        # Confirmation button
        confirm_button = ttk.Button(wizard, text="Start Your Day", command=lambda: confirm_setup())
        confirm_button.pack(pady=20)
        
        def confirm_setup():
            # Validate and save input
            intention = intention_entry.get().strip()[:28]
            if not intention:
                messagebox.showwarning("Input Required", "Please enter a daily intention")
                return
            
            goals = []
            for entry in goal_entries:
                goal = entry.get().strip()[:28]
                if goal:
                    goals.append(goal)
            
            if not goals:
                messagebox.showwarning("Input Required", "Please enter at least one goal")
                return
            
            try:
                pomodoro_time = int(time_entry.get())
                if pomodoro_time <= 0:
                    raise ValueError("Time must be positive")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid number for Pomodoro time")
                return
            
            # Save the settings
            self.daily_intention = intention
            self.goals = goals
            self.original_pomodoro_time = pomodoro_time * 60
            self.pomodoro_time = self.original_pomodoro_time
            self.break_time = max(6 * 60, int(self.pomodoro_time * 0.2))  # 6 minutes or 20% of pomodoro time
            
            # Initialize timer
            self.time_remaining = self.pomodoro_time // 3  # First interval is 1/3 of pomodoro time
            self.update_timer_display()
            
            # Setup the expanded view
            self.setup_expanded_view()
            
            # Create log file for the day if it doesn't exist
            self.ensure_log_file_exists()
            
            # Close the wizard
            wizard.destroy()
        
        # Give focus to the first entry
        intention_entry.focus_set()
    
    def setup_expanded_view(self):
        # Clear any existing widgets
        for widget in self.expanded_frame.winfo_children():
            widget.destroy()
        
        # Daily intention display
        intention_frame = ttk.Frame(self.expanded_frame)
        intention_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(intention_frame, text="Daily Intention:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(intention_frame, text=self.daily_intention, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Goals display with checkboxes
        goals_frame = ttk.Frame(self.expanded_frame)
        goals_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(goals_frame, text="Goals:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5)
        
        for i, goal in enumerate(self.goals):
            if goal in self.completed_goals:
                continue
            
            goal_frame = ttk.Frame(goals_frame)
            goal_frame.pack(fill=tk.X, pady=2)
            
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(goal_frame, text=goal, variable=var, 
                               command=lambda g=goal, v=var: self.goal_completed(g, v))
            cb.pack(side=tk.LEFT, padx=5)
        
        # Completed goals (strikethrough)
        if self.completed_goals:
            completed_frame = ttk.Frame(self.expanded_frame)
            completed_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(completed_frame, text="Completed:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5)
            
            for goal in self.completed_goals:
                ttk.Label(completed_frame, text=f"✓ {goal}", foreground="green").pack(anchor=tk.W, padx=15)
        
        # Status display
        status_frame = ttk.Frame(self.expanded_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text=f"Pomodoros completed: {self.total_pomodoros_completed}").pack(side=tk.LEFT, padx=5)
        
        # Add goal button (if all goals are completed)
        if all(goal in self.completed_goals for goal in self.goals) and self.goals:
            add_goal_button = ttk.Button(self.expanded_frame, text="Add New Goal", 
                                       command=self.add_new_goal)
            add_goal_button.pack(pady=10)
    
    def toggle_expand(self):
        if self.expanded:
            self.expanded_frame.pack_forget()
            self.expand_button.config(text="⬇️")
            
            # Restore original window size
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            window_width = int(screen_width * 0.1)
            window_height = int(screen_height * 0.07)
            self.root.geometry(f"{window_width}x{window_height}")
        else:
            self.expanded_frame.pack(fill=tk.BOTH, expand=True)
            self.expand_button.config(text="⬆️")
            
            # Expand window
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            window_width = int(screen_width * 0.2)
            window_height = int(screen_height * 0.3)
            self.root.geometry(f"{window_width}x{window_height}")
            
            # Refresh the expanded view content
            self.setup_expanded_view()
        
        self.expanded = not self.expanded
    
    def goal_completed(self, goal, var):
        if var.get():
            # Ask for remarks
            remarks = simpledialog.askstring("Goal Completed", 
                                          f"Remarks for completing: {goal}", 
                                          parent=self.root)
            
            # Add to completed goals
            if goal not in self.completed_goals:
                self.completed_goals.append(goal)
            
            # Log the completion
            self.log_activity("goal_completed", goal, remarks)
            
            # Refresh the expanded view
            self.setup_expanded_view()
            
            # Check if all goals are completed
            if all(goal in self.completed_goals for goal in self.goals):
                self.check_day_finished()
    
    def check_day_finished(self):
        # Ask if day is finished
        if messagebox.askyesno("Day Finished?", 
                             "All goals completed! Is your day finished?"):
            self.show_end_of_day_dialog()
    
    def show_end_of_day_dialog(self):
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("End of Day Assessment")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Daily intention review
        ttk.Label(dialog, text=f"Your daily intention:", font=("Arial", 12)).pack(pady=(20, 5))
        ttk.Label(dialog, text=self.daily_intention, font=("Arial", 12, "bold")).pack(pady=(0, 15))
        
        # Rating
        ttk.Label(dialog, text="How well did you achieve your intention? (1-10)", 
                font=("Arial", 12)).pack(pady=(15, 5))
        
        rating_frame = ttk.Frame(dialog)
        rating_frame.pack(pady=10)
        
        rating_var = tk.IntVar(value=5)
        rating_scale = ttk.Scale(rating_frame, from_=1, to=10, variable=rating_var, 
                               orient=tk.HORIZONTAL, length=200)
        rating_scale.pack(side=tk.LEFT)
        
        rating_label = ttk.Label(rating_frame, text="5")
        rating_label.pack(side=tk.LEFT, padx=10)
        
        def update_rating_label(event):
            rating_label.config(text=str(int(rating_var.get())))
        
        rating_scale.bind("<Motion>", update_rating_label)
        
        # Comments
        ttk.Label(dialog, text="Additional comments:", font=("Arial", 12)).pack(pady=(15, 5))
        comments_text = scrolledtext.ScrolledText(dialog, width=40, height=5)
        comments_text.pack(pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(pady=20)
        
        save_button = ttk.Button(buttons_frame, text="Save & Close", 
                               command=lambda: save_and_close())
        save_button.pack(side=tk.LEFT, padx=10)
        
        restart_button = ttk.Button(buttons_frame, text="Start New Day", 
                                  command=lambda: restart_day())
        restart_button.pack(side=tk.LEFT, padx=10)
        
        def save_and_close():
            # Save the end-of-day assessment
            rating = int(rating_var.get())
            comments = comments_text.get("1.0", tk.END).strip()
            
            # Log the end of day
            self.log_activity("end_of_day", f"Rating: {rating}", comments)
            
            # Close dialog and app
            dialog.destroy()
            self.root.destroy()
        
        def restart_day():
            # Save the current assessment
            rating = int(rating_var.get())
            comments = comments_text.get("1.0", tk.END).strip()
            
            # Log the end of day
            self.log_activity("end_of_day", f"Rating: {rating}", comments)
            
            # Reset app state
            self.daily_intention = ""
            self.goals = []
            self.completed_goals = []
            self.total_pomodoros_completed = 0
            self.pomodoro_count = 0
            self.current_interval = 0
            self.paused = True
            
            # Close dialog and restart
            dialog.destroy()
            self.show_setup_wizard()
    
    def add_new_goal(self):
        # Ask for a new goal
        new_goal = simpledialog.askstring("New Goal", 
                                       "Enter a new goal (max 28 chars):", 
                                       parent=self.root)
        
        if new_goal:
            self.goals.append(new_goal[:28])
            self.setup_expanded_view()
    
    def toggle_pause(self):
        if not self.running:
            # Start the timer
            self.running = True
            self.paused = False
            self.start_pause_button.config(text="Pause")
            
            # Start timer in a new thread
            self.timer_thread = threading.Thread(target=self.run_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
        else:
            # Toggle pause state
            self.paused = not self.paused
            
            if self.paused:
                self.start_pause_button.config(text="Resume")
                # Log pause event
                reason = simpledialog.askstring("Pause", 
                                           "Reason for pausing:", 
                                           parent=self.root)
                if reason:
                    self.log_activity("pause", "Timer paused", reason)
            else:
                self.start_pause_button.config(text="Pause")
    
    def open_gedit(self):
        try:
            os.system("gedit &")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open gedit: {e}")
    
    def minimize_app(self):
        self.root.iconify()
    
    def toggle_concentration(self):
        self.playing_concentration = not self.playing_concentration
        
        if self.playing_concentration:
            self.concentration_button.config(text="🔇")
            self.play_concentration_sound()
        else:
            self.concentration_button.config(text="🔊")
            pygame.mixer.stop()
    
    def play_concentration_sound(self):
        try:
            concentration_sound = os.path.join(self.sound_folder, "2_min_concetration.wav")
            sound = pygame.mixer.Sound(concentration_sound)
            sound.play(loops=-1)  # Loop continuously
        except Exception as e:
            messagebox.showerror("Error", f"Could not play concentration sound: {e}")
            self.playing_concentration = False
            self.concentration_button.config(text="🔊")
    
    def play_interval_sound(self):
        try:
            interval_sound = os.path.join(self.sound_folder, "short_0.333_pom_cue_bell.wav")
            pygame.mixer.Sound(interval_sound).play()
        except Exception as e:
            messagebox.showerror("Error", f"Could not play interval sound: {e}")
    
    def play_break_sound(self):
        try:
            break_sound = os.path.join(self.sound_folder, "break_meditate_cue_bell.wav")
            pygame.mixer.Sound(break_sound).play()
        except Exception as e:
            messagebox.showerror("Error", f"Could not play break sound: {e}")
    
    def run_timer(self):
        while self.running:
            if not self.paused:
                # Update time remaining
                if self.time_remaining > 0:
                    self.time_remaining -= 1
                    
                    # Update UI
                    self.root.after(0, self.update_timer_display)
                    
                    # Sleep for a second
                    time.sleep(1)
                else:
                    # End of current interval
                    self.root.after(0, self.handle_interval_end)
                    
                    # Sleep to prevent CPU hogging
                    time.sleep(0.5)
            else:
                # Paused, just sleep
                time.sleep(0.5)
    
    def handle_interval_end(self):
        # Play appropriate sound
        if self.current_interval < 3:  # End of work interval
            self.play_interval_sound()
        else:  # End of break
            self.play_break_sound()
        
        # Move to next interval
        self.current_interval = (self.current_interval + 1) % 4
        
        # Update pomodoro count and time if needed
        if self.current_interval == 0:
            self.pomodoro_count += 1
            self.total_pomodoros_completed += 1
            
            # Log completed pomodoro
            self.log_activity("pomodoro_completed", f"Pomodoro #{self.total_pomodoros_completed}", "")
            
            # Adaptive pomodoro timing
            if self.pomodoro_count % 4 == 0:
                # After every 4 pomodoros, adjust time
                if self.pomodoro_count <= 4:
                    self.pomodoro_time = self.original_pomodoro_time
                elif self.pomodoro_count <= 8:
                    self.pomodoro_time = int(self.original_pomodoro_time * 0.9)  # 10% reduction
                else:
                    self.pomodoro_time = int(self.original_pomodoro_time * 0.8)  # 20% reduction
        
        # Set new time remaining
        if self.current_interval < 3:  # Work interval (1/3 of pomodoro)
            self.time_remaining = self.pomodoro_time // 3
        else:  # Break
            self.time_remaining = self.break_time
        
        # Update display
        self.update_timer_display()
    
    def update_timer_display(self):
        minutes, seconds = divmod(self.time_remaining, 60)
        timer_text = f"{minutes:02d}:{seconds:02d}"
        
        # Add indicator for work/break
        if self.current_interval < 3:
            status = f"W{self.current_interval+1}"  # Work interval 1, 2, or 3
        else:
            status = "Break"
        
        # Update label
        self.timer_label.config(text=f"{timer_text} ({status})")
        
        # Update title for better visibility when minimized
        self.root.title(f"{timer_text} | Pom #{self.total_pomodoros_completed+1}")
    
    def ensure_log_file_exists(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"focus_log_{today}.csv")
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Event", "Detail", "Remarks"])
                writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                               "day_started", f"Intention: {self.daily_intention}", 
                               f"Goals: {', '.join(self.goals)}"])
    
    def log_activity(self, event_type, detail, remarks):
        try:
            self.ensure_log_file_exists()
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    event_type,
                    detail,
                    remarks
                ])
        except Exception as e:
            print(f"Error logging activity: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FocusReminderApp(root)
    root.mainloop()
