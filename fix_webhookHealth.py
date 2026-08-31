import re
with open('runtime/webhookHealth.py', 'r') as f:
    content = f.read()

new_func = '''    async def _cleanupMissingDivisionHubMessage(self, *, messageId: int) -> bool:
        return False'''
        
content = re.sub(r'    async def _cleanupMissingDivisionHubMessage\(.*?\)\s*->\s*bool:.*?(?=\n\n)', new_func, content, flags=re.MULTILINE|re.DOTALL)

with open('runtime/webhookHealth.py', 'w') as f:
    f.write(content)
