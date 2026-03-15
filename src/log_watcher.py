import time
import os
import pandas as pd
import pickle
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

# Add src to path
sys.path.append(os.path.dirname(__file__))

from feature_eng import FeatureEngineer

class LogHandler(FileSystemEventHandler):
    def __init__(self, file_path, model):
        self.file_path = file_path
        self.model = model
        self.last_position = 0
        self.columns = None  # Cached header columns

        # Initialize last position to end of file to avoid re-reading entire file on startup
        if os.path.exists(file_path):
            self.last_position = os.path.getsize(file_path)
            try:
                header_df = pd.read_csv(file_path, nrows=0)
                self.columns = header_df.columns  # Read ONCE, cache forever
            except Exception as e:
                print(f"Warning: could not read header: {e}")
            print(f"LogWatcher initialized. Watching {file_path} starting from byte {self.last_position}")

    def on_modified(self, event):
        if event.src_path == self.file_path:
            self.process_new_lines()

    def process_new_lines(self):
        try:
            current_size = os.path.getsize(self.file_path)
            if current_size < self.last_position:
                # File was truncated or rotated
                self.last_position = 0
            
            if current_size > self.last_position:
                with open(self.file_path, 'r') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()
                
                if new_lines:
                    print(f"Detected {len(new_lines)} new lines.")
                    self.analyze_lines(new_lines)
        except Exception as e:
            print(f"Error processing log file: {e}")

    def analyze_lines(self, lines):
        if self.columns is None:
            print("No column headers cached. Skipping.")
            return
        columns = self.columns

        from io import StringIO
        data = StringIO(''.join(lines))
        
        try:
            # Read new data using the columns
            df = pd.read_csv(data, names=columns, header=None)
            
            # Feature Engineering
            fe = FeatureEngineer(df)
            X = fe.get_inference_features()
            
            # Align features with model
            if hasattr(self.model, 'feature_names_in_'):
                expected_features = self.model.feature_names_in_
                
                # Ensure all expected columns exist
                for col in expected_features:
                    if col not in X.columns:
                        X[col] = 0
                
                X = X[expected_features]
                
                # Inference
                predictions = self.model.predict(X)
                
                # Check for attacks
                for i, pred in enumerate(predictions):
                    if pred == 1:
                        print(f"🚨 [ALERT] Attack Detected! Payload: {lines[i].strip()[:50]}...")
                        # In a real system, we would write to alerts.json or trigger an API
                        
        except Exception as e:
            print(f"Error analyzing lines: {e}")

class LogWatcher:
    def __init__(self, log_path, model_path):
        self.log_path = log_path
        self.model_path = model_path
        self.observer = Observer()
        self.model = self.load_model()

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model = pickle.load(f)
                print("LogWatcher: Model loaded.")
                return model
            else:
                print("LogWatcher: Model not found.")
                return None
        except Exception as e:
            print(f"LogWatcher: Error loading model: {e}")
            return None

    def start(self):
        if not self.model:
            print("LogWatcher: Cannot start without model.")
            return

        if not os.path.exists(self.log_path):
            print(f"LogWatcher: Log file {self.log_path} does not exist. Waiting for it to be created...")
            # We can still start the observer on the directory
            
        event_handler = LogHandler(self.log_path, self.model)
        log_dir = os.path.dirname(self.log_path)
        
        if not os.path.exists(log_dir):
             # Try to use current dir if log dir doesn't exist (fallback)
             log_dir = "."

        self.observer.schedule(event_handler, path=log_dir, recursive=False)
        self.observer.start()
        print(f"LogWatcher started. Monitoring {self.log_path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

def start_watcher_thread(log_path, model_path):
    watcher = LogWatcher(log_path, model_path)
    thread = threading.Thread(target=watcher.start)
    thread.daemon = True
    thread.start()
    return watcher

if __name__ == "__main__":
    # Test run
    LOG_PATH = os.getenv("LOG_PATH", "logs/logs.csv")
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'best_model.pkl')
    
    watcher = LogWatcher(LOG_PATH, MODEL_PATH)
    watcher.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
