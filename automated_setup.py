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
        
        # Get the directory where the setup script is running
        if getattr(sys, 'frozen', False):
            self.setup_dir = Path(sys._MEIPASS)
        else:
            self.setup_dir = Path(__file__).parent
            
        self.app_dir = self.setup_dir / "app"
        self.extension_dir = self.setup_dir / "extension"
        
        # Get extension ID from the bundled extension
        self.EXTENSION_ID = self.get_extension_id()
        self.EXTENSION_URL = f"https://chrome.google.com/webstore/detail/{self.EXTENSION_ID}"

    def get_extension_id(self):
        """Extract extension ID from the bundled extension's manifest"""
        try:
            # First try unpacked extension
            manifest_path = self.extension_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    if 'key' in manifest:
                        # If extension is unpacked, calculate ID from key
                        return self.calculate_extension_id(manifest['key'])
            
            # Try packed extension (.crx file)
            crx_path = self.extension_dir / "extension.crx"
            if crx_path.exists():
                with zipfile.ZipFile(crx_path) as zf:
                    with zf.open('manifest.json') as f:
                        manifest = json.load(f)
                        if 'key' in manifest:
                            return self.calculate_extension_id(manifest['key'])
            
            raise Exception("Could not find extension manifest")
            
        except Exception as e:
            print(f"Error getting extension ID: {e}")
            # Fallback to a default ID if needed
            return "your_default_extension_id"

    def calculate_extension_id(self, key):
        """Calculate extension ID from public key"""
        import base64
        import hashlib
        
        # Decode the key
        decoded_key = base64.b64decode(key)
        
        # Calculate SHA256 hash
        sha = hashlib.sha256(decoded_key).hexdigest()
        
        # Convert to Chrome extension ID format (first 32 chars)
        extension_id = ''.join(chr(ord('a') + (int(x, 16) % 26)) if x.isdigit() 
                             else x.lower() for x in sha[:32])
        
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
        print("Opening Chrome extension page...")
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
            
            exe_source = self.get_resource_path(os.path.join("app", "dist", exe_name))
            
            if not os.path.exists(exe_source):
                raise FileNotFoundError(f"Could not find executable at {exe_source}")
            
            # Copy the executable to installation directory
            shutil.copy2(exe_source, install_dir)
            exe_dest = os.path.join(install_dir, exe_name)
            
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
        self.root = tk.Tk()
        self.root.title("Speech Recognition Setup")
        self.root.geometry("400x250")
        self.setup = AutomatedSetup()
        self.create_widgets()

    def create_widgets(self):
        # Create and pack widgets
        self.status_label = ttk.Label(self.root, text="Preparing installation...", padding=10)
        self.status_label.pack()

        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=20)

        self.detail_label = ttk.Label(self.root, text="", padding=10)
        self.detail_label.pack()

    def update_status(self, message, progress):
        self.status_label["text"] = message
        self.progress["value"] = progress
        self.root.update()

    def run_setup(self):
        try:
            # Check Chrome
            self.update_status("Checking Chrome installation...", 10)
            if not self.setup.check_chrome_installed():
                messagebox.showerror("Error", "Google Chrome is not installed. Please install Chrome first.")
                self.root.quit()
                return

            # Install application
            self.update_status("Installing application...", 30)
            install_dir = self.setup.install_application()

            # Setup native messaging
            self.update_status("Configuring native messaging...", 50)
            manifest_path = self.setup.setup_native_messaging(install_dir)

            # Create shortcuts
            self.update_status("Creating shortcuts...", 70)
            self.setup.create_shortcuts(install_dir)

            # Verify installation
            self.update_status("Verifying installation...", 90)
            if not self.setup.verify_installation(install_dir, manifest_path):
                raise Exception("Installation verification failed")

            # Install Chrome extension
            self.update_status("Opening Chrome extension page...", 95)
            self.setup.install_chrome_extension()

            self.update_status("Installation completed successfully!", 100)
            messagebox.showinfo("Success", "Installation completed successfully!\n\nPlease install the Chrome extension to complete the setup.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
        finally:
            self.root.quit()

    def start(self):
        self.root.after(100, self.run_setup)
        self.root.mainloop()

def main():
    run_as_admin()
    gui = SetupGUI()
    gui.start()

if __name__ == "__main__":
    main() 