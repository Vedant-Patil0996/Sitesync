import glob
import os

files = glob.glob('c:/MyFiles/Desktop/Development/Sitesync/backend/ivr/*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content.replace('\\\"', '\"')
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Fixed {f}")
