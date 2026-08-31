import os
import re

def filter_file(filepath, patterns_to_remove):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    out_lines = []
    skip_until_paren = False
    for line in lines:
        if skip_until_paren:
            if ')' in line:
                skip_until_paren = False
            continue
            
        remove = False
        for p in patterns_to_remove:
            if re.search(p, line):
                remove = True
                if '(' in line and ')' not in line:
                    skip_until_paren = True
                break
        if not remove:
            out_lines.append(line)
            
    with open(filepath, 'w') as f:
        f.writelines(out_lines)

# Fix API/EndPoints.py
filter_file('API/EndPoints.py', [
    r'from features\.staff\.sessions\.service import attemptClockIn',
    r'from features\.staff\.sessions\.viewRuntime import requestSessionMessageUpdate'
])

# Fix bot.py
filter_file('bot.py', [
    r'from features\.staff\.recruitment import',
    r'from features\.staff\.trainingLog import',
    r'from features\.staff\.sessions import',
    r'from features\.staff\.sessions\.Roblox import',
    r'from features\.operations\.serverSafety import',
    r'janeIdentityWeb as runtimeJaneIdentityWeb',
    r'johnEventRuntime as runtimeJohnEventRuntime',
    r'orbatAudit as runtimeOrbatAudit',
    r'trainingLogRuntime as runtimeTrainingLogRuntime',
    r'gamblingApi as runtimeGamblingApi',
    r'orbatAuditRuntime = runtimeOrbatAudit',
    r'janeIdentityWeb = runtimeJaneIdentityWeb',
    r'johnEventRuntime = runtimeJohnEventRuntime',
    r'trainingLogRuntime = runtimeTrainingLogRuntime',
    r'gamblingApi = runtimeGamblingApi',
    r'recruitmentService\.',
    r'trainingLogService\.',
    r'sessionService\.',
    r'runtimeJaneIdentityWeb\.',
    r'runtimeOrbatAudit\.',
    r'runtimeTrainingLogRuntime\.',
    r'runtimeJohnEventRuntime\.',
    r'runtimeGamblingApi\.'
])

# Stub robloxUsers in bestOfCog, utility
filter_file('cogs/community/bestOfCog.py', [r'from features\.staff\.sessions\.Roblox import robloxUsers'])
filter_file('runtime/prefix/utility.py', [r'from features\.staff\.sessions\.Roblox import robloxUsers'])
filter_file('runtime/webhookHealth.py', [r'from features\.staff\.applications import service as applicationsService'])
