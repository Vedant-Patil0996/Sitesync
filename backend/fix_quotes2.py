import glob

files = glob.glob('c:/MyFiles/Desktop/Development/Sitesync/backend/ivr/*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace \\" with just " (which might break if it's already inside double quotes, so let's use single quotes)
    # Actually, in demo_logger.py it's: print(f"[CALL {call_sid[-6:]}] Heard:     \\"{heard}\\"")
    # If we replace \\" with ' we get: print(f"[CALL {call_sid[-6:]}] Heard:     '{heard}'")
    new_content = content.replace('\\\\"', "'")
    # Also replace \\n with \n
    new_content = new_content.replace('\\\\n', '\\n')
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Fixed {f}")
