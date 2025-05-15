import re

# Load the combined file
input_filename = 'cleaned_cmds_2.txt'
output_filename = 'me_trainning.txt'

# Read the content of the file
with open(input_filename, 'r') as file:
    text = file.read()

# Basic cleaning process
def clean_text(text):
    # Remove extra whitespace (leading/trailing and between words)
    text = re.sub(r'\s+', ' ', text.strip())

    # Convert to lowercase (optional)
    text = text.lower()

    # Remove special characters (optional)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    return text

# Apply cleaning function
cleaned_text = clean_text(text)

# Save the cleaned text to a new file
with open(output_filename, 'w') as output_file:
    output_file.write(cleaned_text)

print(f"Cleaning completed. Cleaned content is saved to {output_filename}")

