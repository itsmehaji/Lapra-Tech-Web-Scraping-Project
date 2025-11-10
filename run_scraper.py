import subprocess
import sys

# Run scraper with input
process = subprocess.Popen([sys.executable, 'scraper.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Provide input
inputs = "GOA\n\n"  # State GOA, then empty for city if asked
stdout, stderr = process.communicate(input=inputs)

print("STDOUT:")
print(stdout)
print("STDERR:")
print(stderr)
print("Return code:", process.returncode)