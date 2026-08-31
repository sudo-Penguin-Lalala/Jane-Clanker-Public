import re

with open('runtime/prefix/utility.py', 'r') as f:
    content = f.read()

new_func = '''async def _pairDbNamesLookup(discordUserId: int, guildId: int) -> _PairDbNamesLookupResult:
    return _PairDbNamesLookupResult(
        robloxUsername="",
        errorMessage="Roblox lookups have been removed."
    )'''

content = re.sub(r'async def _pairDbNamesLookup\(.*?\)\s*->\s*_PairDbNamesLookupResult:.*?(?=\n\n\n)', new_func, content, flags=re.MULTILINE|re.DOTALL)

with open('runtime/prefix/utility.py', 'w') as f:
    f.write(content)
