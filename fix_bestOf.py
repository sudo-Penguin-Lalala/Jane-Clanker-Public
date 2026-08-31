with open('cogs/community/bestOfCog.py', 'r') as f:
    lines = f.readlines()

out = lines[:801]
out.append('        for member in candidateMembersByUserId.values():\n')
out.append('            fallbackName = _cleanBestOfDisplayName(str(member.display_name or member.name or f"User {member.id}"))\n')
out.append('            out[int(member.id)] = fallbackName\n')
out.extend(lines[845:])

with open('cogs/community/bestOfCog.py', 'w') as f:
    f.writelines(out)
