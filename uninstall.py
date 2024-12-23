import os
import sys
import shutil
import winreg
from pathlib import Path
import ctypes

class Uninstaller:
    def __init__(self):
        self.APP_NAME = "com.your.speechrecognition"
        self.install_dir = self.get_install_directory()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        if sys.platform.startswith('win'):
            if not is_admin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()

    def get_install_directory(self):
        if sys.platform.startswith('win'):
            return os.path.join(os.environ.get('LOCALAPPDATA'), 'SpeechRecognition')
        elif sys.platform.startswith('darwin'):
            return '/Applications/SpeechRecognition.app'
        raise OSError("Unsupported operating system")

    def remove_native_messaging_host(self):
        """Remove native messaging host configuration"""
        try:
            if sys.platform.startswith('win'):
                # Remove manifest file
                manifest_path = Path(os.environ['LOCALAPPDATA']) / "Google" / "Chrome" / "NativeMessagingHosts" / f"{self.APP_NAME}.json"
                if manifest_path.exists():
                    manifest_path.unlink()

                # Remove registry entry
                try:
                    reg_key = rf"SOFTWARE\Google\Chrome\NativeMessagingHosts\{self.APP_NAME}"
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_key)
                except WindowsError:
                    pass  # Key might not exist

            elif sys.platform.startswith('darwin'):
                manifest_path = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts" / f"{self.APP_NAME}.json"
                if manifest_path.exists():
                    manifest_path.unlink()

            print("Removed native messaging host configuration")
            return True

        except Exception as e:
            print(f"Error removing native messaging host: {e}")
            return False

    def remove_desktop_shortcut(self):
        """Remove desktop shortcut"""
        try:
            if sys.platform.startswith('win'):
                import winshell
                desktop = winshell.desktop()
                shortcut_path = os.path.join(desktop, "Speech Recognition.lnk")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    print("Removed desktop shortcut")
        except Exception as e:
            print(f"Error removing shortcut: {e}")

    def remove_application_files(self):
        """Remove the installed application"""
        try:
            if os.path.exists(self.install_dir):
                shutil.rmtree(self.install_dir)
                print(f"Removed application files from {self.install_dir}")
            return True
        except Exception as e:
            print(f"Error removing application files: {e}")
            return False

    def uninstall(self):
        print("Starting uninstallation...")
        
        # Remove native messaging configuration
        self.remove_native_messaging_host()
        
        # Remove desktop shortcut
        self.remove_desktop_shortcut()
        
        # Remove application files
        self.remove_application_files()
        
        print("\nUninstallation complete!")
        print("Note: Please remove the Chrome extension manually from chrome://extensions")
        input("Press Enter to exit...")

def main():
    uninstaller = Uninstaller()
    uninstaller.uninstall()

if __name__ == "__main__":
    main() 