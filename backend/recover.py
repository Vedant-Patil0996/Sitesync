import json
import glob
import os

transcript_file = r"C:\Users\Dell_owner\.gemini\antigravity-ide\brain\e810efab-2263-437b-b349-58d03385a7b1\.system_generated\logs\transcript_full.jsonl"
file_contents = {}

with open(transcript_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'PLANNER_RESPONSE':
                for tool_call in data.get('tool_calls', []):
                    if tool_call.get('name') == 'default_api:write_to_file':
                        args = tool_call.get('arguments', {})
                        target = args.get('TargetFile', '').replace('\\', '/')
                        if 'backend/ivr/' in target:
                            file_contents[target] = args.get('CodeContent')
        except:
            pass

for target, content in file_contents.items():
    if content:
        # Don't overwrite tool_adapters.py since the user edited it!
        if 'tool_adapters.py' in target:
            continue
        try:
            with open(target, 'w', encoding='utf-8') as out:
                # the transcript might have "gemini-1.5-flash", replace it
                content = content.replace('gemini-1.5-flash', 'gemini-2.0-flash')
                out.write(content)
            print(f"Recovered {target}")
        except Exception as e:
            print(f"Failed to recover {target}: {e}")
