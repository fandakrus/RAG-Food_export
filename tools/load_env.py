import os

def load_dotenv(file_path):
    with open(file_path) as f:
        for line in f:
            # Remove any leading/trailing whitespace
            line = line.strip()
            if line and not line.startswith('#'):  # Ignore empty lines and comments
                key, value = line.split('=', 1)
                # Remove surrounding quotes from the value if they exist
                value = value.strip('"').strip("'")
                os.environ[key] = value
                print(f"Exported: {key}={value}")

if __name__ == "__main__":
    dotenv_path = '.env'  # Path to your .env file
    load_dotenv(dotenv_path)