import subprocess
import sys

def main():
    # Install requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run the Streamlit app
    subprocess.check_call([sys.executable, "-m", "streamlit", "run", "main.py"])

if __name__ == "__main__":
    main()