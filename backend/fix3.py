content = open('c:/MyFiles/Desktop/Development/Sitesync/backend/ivr/webhook.py', encoding='utf-8').read()
content = content.replace('\\\"application/xml\\\"', '\"application/xml\"')
open('c:/MyFiles/Desktop/Development/Sitesync/backend/ivr/webhook.py', 'w', encoding='utf-8').write(content)
