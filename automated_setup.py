import os
import sys
import json
import shutil
import webbrowser
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import zipfile
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if sys.platform.startswith('win'):
        if not is_admin():
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

class AutomatedSetup:
    def __init__(self):
        self.APP_NAME = "com.your.speechrecognition"
        self.gui = None  # Initialize gui attribute as None
        
        # Get the directory where the setup script is running
        if getattr(sys, 'frozen', False):
            self.setup_dir = Path(sys._MEIPASS)
        else:
            self.setup_dir = Path(__file__).parent
            
        self.app_dir = self.setup_dir / "app"
        self.extension_dir = self.setup_dir / "extension"
        
        # Don't get extension ID in init
        self.EXTENSION_ID = None
        self.EXTENSION_URL = None

    def initialize_extension(self):
        """Initialize extension ID and URL after GUI is set up"""
        self.EXTENSION_ID = self.get_extension_id()
        self.EXTENSION_URL = f"https://chrome.google.com/webstore/detail/{self.EXTENSION_ID}"

    def get_extension_id(self):
        """Get ID from installed Chrome extension using manifest key"""
        try:
            # Read our manifest to get the key
            manifest_path = self.extension_dir / "manifest.json"
            print(f"\nLooking for manifest at: {manifest_path}")
            
            with open(manifest_path) as f:
                manifest = json.load(f)
                key = manifest.get('key')
                if not key:
                    raise Exception("Extension key not found in manifest.json")
                print(f"Found key in manifest: {key[:32]}...")

            # Calculate the expected extension ID
            expected_id = self.calculate_extension_id(key)
            print(f"\nCalculated extension ID: {expected_id}")

            # Verify the extension exists in Chrome
            if sys.platform.startswith('win'):
                chrome_user_data = Path(os.environ['LOCALAPPDATA']) / "Google" / "Chrome" / "User Data"
            else:
                chrome_user_data = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"

            print(f"Searching for extension in: {chrome_user_data}")

            profiles = ['Default'] + [f'Profile {i}' for i in range(1, 10)]
            
            for profile in profiles:
                print(f"\nChecking profile: {profile}")
                
                pref_files = [
                    chrome_user_data / profile / "Secure Preferences",
                    chrome_user_data / profile / "Preferences"
                ]
                
                for pref_file in pref_files:
                    if pref_file.exists():
                        try:
                            # Try different encodings
                            for encoding in ['utf-8', 'utf-8-sig', 'latin1']:
                                try:
                                    with open(pref_file, encoding=encoding) as f:
                                        print(f"Reading: {pref_file} with {encoding} encoding")
                                        prefs = json.load(f)
                                        
                                        # Simply check if the ID exists in extensions.settings
                                        extensions = prefs.get('extensions', {}).get('settings', {})
                                        print(f"Found {len(extensions)} extensions")
                                        print(f"Available extension IDs: {list(extensions.keys())}")
                                        
                                        if expected_id in extensions:
                                            print(f"\n✓ Found extension {expected_id} in profile: {profile}")
                                            self.gui.detail_label["text"] = f"Found extension in {profile}"
                                            return expected_id
                                except UnicodeDecodeError:
                                    continue
                        except Exception as e:
                            print(f"Error reading {pref_file}: {e}")
                            continue

            raise Exception("Extension not found. Please install the Chrome extension first.")

        except Exception as e:
            print(f"Error getting extension ID: {e}")
            raise

    def calculate_extension_id(self, key):
        """Calculate extension ID from public key"""
        import base64
        import hashlib
        
        print(f"\nCalculating extension ID from key:")
        print(f"Input key: {key[:32]}...")
        
        # Decode the key
        decoded_key = base64.b64decode(key)
        print(f"Decoded key length: {len(decoded_key)} bytes")
        
        # Calculate SHA256 hash
        sha = hashlib.sha256(decoded_key).hexdigest()
        print(f"SHA256 hash: {sha[:32]}...")
        
        # Convert to Chrome extension ID format (first 32 chars)
        extension_id = ''.join(chr(ord('a') + (int(x, 16) % 26)) if x.isdigit() 
                             else x.lower() for x in sha[:32])
        print(f"Calculated extension ID: {extension_id}")
        
        return extension_id

    def check_chrome_installed(self):
        """Check if Chrome is installed"""
        chrome_paths = {
            'win32': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'darwin': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        }
        return os.path.exists(chrome_paths.get(sys.platform, ''))

    def install_chrome_extension(self):
        """Open Chrome Web Store page for extension installation"""
        if not self.EXTENSION_URL:
            raise Exception("Extension URL not set")
        print(f"Opening Chrome extension URL: {self.EXTENSION_URL}")
        webbrowser.open(self.EXTENSION_URL)
        return True

    def install_application(self):
        """Install the bundled application"""
        install_dir = self.get_install_directory()
        
        try:
            # Create installation directory if it doesn't exist
            os.makedirs(install_dir, exist_ok=True)
            
            # Get path to the bundled executable
            if sys.platform.startswith('win'):
                exe_name = "speech_recognition_app.exe"
            else:
                exe_name = "speech_recognition_app"
            
            # Look for the executable in the bundled resources
            exe_source = self.get_resource_path(os.path.join("app", "dist", exe_name))
            
            if not os.path.exists(exe_source):
                raise FileNotFoundError(f"Could not find executable at {exe_source}")
            
            # Copy only the executable file to installation directory
            exe_dest = os.path.join(install_dir, exe_name)
            shutil.copy2(exe_source, exe_dest)
            
            # Set executable permissions on macOS
            if sys.platform.startswith('darwin'):
                os.chmod(exe_dest, 0o755)
            
            print(f"Application installed to: {install_dir}")
            return install_dir
            
        except Exception as e:
            print(f"Error installing application: {e}")
            raise

    def get_install_directory(self):
        """Get the appropriate installation directory for the OS"""
        if sys.platform.startswith('win'):
            return os.path.join(os.environ.get('LOCALAPPDATA'), 'SpeechRecognition')
        elif sys.platform.startswith('darwin'):
            return '/Applications/SpeechRecognition.app'
        raise OSError("Unsupported operating system")

    def setup_native_messaging(self, app_path):
        """Setup native messaging host"""
        # Get the path to the executable
        if sys.platform.startswith('win'):
            executable = "speech_recognition_app.exe"
        else:
            executable = "speech_recognition_app"
        
        executable_path = str(Path(app_path) / executable)  # Simplified path
        
        manifest = {
            "name": self.APP_NAME,
            "description": "Speech Recognition Native Messaging Host",
            "path": executable_path,
            "type": "stdio",
            "allowed_origins": [f"chrome-extension://{self.EXTENSION_ID}/"]
        }

        if sys.platform.startswith('win'):
            manifest_dir = Path(os.environ['LOCALAPPDATA']) / "Google" / "Chrome" / "NativeMessagingHosts"
            # Also add registry entry
            self.add_windows_registry(manifest_dir / f"{self.APP_NAME}.json")
        else:  # macOS
            manifest_dir = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"

        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{self.APP_NAME}.json"

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        if sys.platform.startswith('darwin'):
            os.chmod(manifest_path, 0o644)
            
        return manifest_path

    def add_windows_registry(self, manifest_path):
        """Add Windows registry entry for native messaging host"""
        if sys.platform.startswith('win'):
            try:
                import winreg
                reg_key = rf"SOFTWARE\Google\Chrome\NativeMessagingHosts\{self.APP_NAME}"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, str(manifest_path))
            except Exception as e:
                print(f"Error adding registry entry: {e}")
                raise

    def create_shortcuts(self, app_path):
        """Create desktop shortcuts"""
        if sys.platform.startswith('win'):
            try:
                import winshell
                from win32com.client import Dispatch
                desktop = winshell.desktop()
                path = os.path.join(desktop, "Speech Recognition.lnk")
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = str(Path(app_path) / "speech_recognition_app.exe")
                shortcut.save()
            except Exception as e:
                print(f"Error creating shortcut: {e}")
                raise

    def verify_installation(self, install_dir, manifest_path):
        """Verify that everything is installed correctly"""
        try:
            # Check if application files exist
            app_exists = Path(install_dir).exists()
            
            # Check if manifest exists
            manifest_exists = Path(manifest_path).exists()
            
            if not app_exists or not manifest_exists:
                raise Exception("Installation verification failed")
                
            return True
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

class SetupGUI:
    def __init__(self):
        print("Initializing GUI...")
        self.root = tk.Tk()
        self.root.title("Speech Recognition Setup")
        self.root.geometry("400x400")  # Made taller for new controls
        print("Creating AutomatedSetup instance...")
        self.setup = AutomatedSetup()
        self.setup.gui = self
        print("Creating widgets...")
        self.create_widgets()
        print("GUI initialization complete")

    def create_widgets(self):
        # Extension ID Frame
        ext_frame = ttk.LabelFrame(self.root, text="Chrome Extension ID", padding=10)
        ext_frame.pack(fill='x', padx=10, pady=5)

        # Extension ID Entry
        self.ext_id_var = tk.StringVar()
        self.ext_id_entry = ttk.Entry(ext_frame, textvariable=self.ext_id_var)
        self.ext_id_entry.pack(fill='x', pady=5)

        # Buttons Frame
        btn_frame = ttk.Frame(ext_frame)
        btn_frame.pack(fill='x', pady=5)

        # Auto Detect Button
        self.detect_btn = ttk.Button(btn_frame, text="Auto Detect", command=self.auto_detect_extension)
        self.detect_btn.pack(side='left', padx=5)

        # Continue Button
        self.continue_btn = ttk.Button(btn_frame, text="Continue", command=self.validate_and_continue)
        self.continue_btn.pack(side='right', padx=5)

        # Status Labels
        self.status_label = ttk.Label(self.root, text="Waiting for extension ID...", padding=10)
        self.status_label.pack()

        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=20)

        self.detail_label = ttk.Label(self.root, text="", padding=10, wraplength=350)
        self.detail_label.pack(fill='x', padx=10)

    def auto_detect_extension(self):
        """Try to auto-detect the extension ID"""
        try:
            self.status_label["text"] = "Detecting extension..."
            self.detail_label["text"] = "Searching in Chrome profiles..."
            self.progress["value"] = 10
            self.root.update()

            # Try to detect extension
            extension_id = self.find_extension_id()
            if extension_id:
                self.ext_id_var.set(extension_id)
                self.detail_label["text"] = f"Found extension: {extension_id}"
                self.status_label["text"] = "Extension detected successfully!"
            else:
                self.detail_label["text"] = "Extension not found. Please enter ID manually."
                self.status_label["text"] = "Auto-detection failed"
        except Exception as e:
            self.detail_label["text"] = f"Error: {str(e)}"
            self.status_label["text"] = "Auto-detection failed"

    def find_extension_id(self):
        """Find extension ID in Chrome profiles"""
        if sys.platform.startswith('win'):
            chrome_user_data = Path(os.environ['LOCALAPPDATA']) / "Google" / "Chrome" / "User Data"
        else:
            chrome_user_data = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"

        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 10)]
        
        for profile in profiles:
            pref_file = chrome_user_data / profile / "Preferences"
            
            if pref_file.exists():
                try:
                    with open(pref_file, encoding='utf-8') as f:
                        prefs = json.load(f)
                        extensions = prefs.get('extensions', {}).get('settings', {})
                        
                        # Look for extension with matching name or other criteria
                        for ext_id, ext_data in extensions.items():
                            manifest = ext_data.get('manifest', {})
                            if manifest.get('name') == "Real-time Transcription":
                                return ext_id
                except Exception as e:
                    print(f"Error reading {pref_file}: {e}")
                    continue
        return None

    def validate_and_continue(self):
        """Validate extension ID and continue with setup"""
        extension_id = self.ext_id_var.get().strip()
        if not extension_id:
            messagebox.showerror("Error", "Please enter or detect an extension ID")
            return
            
        # Basic validation of extension ID format
        if not extension_id.isalnum() or len(extension_id) != 32:
            messagebox.showerror("Error", "Invalid extension ID format")
            return

        # Store the ID and set up the extension URL
        self.setup.EXTENSION_ID = extension_id
        self.setup.EXTENSION_URL = f"https://chrome.google.com/webstore/detail/{extension_id}"
        self.run_setup()

    def run_setup(self):
        """Run the setup process with the selected extension ID"""
        print("Starting setup process...")
        try:
            # Use the stored extension ID for the rest of the setup
            self.update_status("Installing application...", 30)
            install_dir = self.setup.install_application()

            self.update_status("Configuring native messaging...", 50)
            manifest_path = self.setup.setup_native_messaging(install_dir)

            self.update_status("Creating shortcuts...", 70)
            self.setup.create_shortcuts(install_dir)

            self.update_status("Verifying installation...", 90)
            if not self.setup.verify_installation(install_dir, manifest_path):
                raise Exception("Installation verification failed")

            self.update_status("Opening Chrome extension page...", 95)
            self.setup.install_chrome_extension()

            self.update_status("Installation completed successfully!", 100)
            messagebox.showinfo("Success", "Installation completed successfully!")
            
        except Exception as e:
            print(f"Setup error: {e}")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
        finally:
            print("Setup process complete")
            self.root.quit()

    def update_status(self, message, progress):
        self.status_label["text"] = message
        self.progress["value"] = progress
        self.root.update()

    def start(self):
        self.root.mainloop()

def main():
    print("Starting setup...")
    try:
        gui = SetupGUI()
        print("Created GUI instance")
        gui.start()
        print("Started GUI")
    except Exception as e:
        print(f"Error during setup: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    print("Script started")
    main() 