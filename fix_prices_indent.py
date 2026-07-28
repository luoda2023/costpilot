"""修复 prices.py 中 list_prices 和 search_prices 的缩进"""
import re

with open('packages/server/api/prices.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 85-113 (list_prices)
# Line 85: @router.get("", ...) - keep
# Line 86: def list_prices( - keep  
# Lines 87-93: params - change 2-space to 4-space
# Line 94: ): - keep
# Lines 95-113: body - change 2-space to 4-space, nested to 8-space

# Find list_prices function range
start_found = False
func_start = -1
func_end = -1

for i, line in enumerate(lines):
    if '@router.get("", response_model=List[PriceUnitOut])' in line:
        func_start = i
        start_found = True
    elif start_found and '@router.get("/search"' in line:
        func_end = i
        break

print(f"list_prices: lines {func_start+1} to {func_end+1}")

# Fix list_prices
for i in range(func_start, func_end):
    line = lines[i]
    stripped = line.lstrip()
    if not stripped:
        continue
    
    leading = len(line) - len(line.lstrip())
    
    # Lines 87-93 (params): currently 2 spaces, should be 4
    if i < func_start + 8:  # param lines
        if leading == 2:
            lines[i] = '    ' + stripped
    # Lines 94+ (body): currently 2 spaces, should be 4
    elif i == func_start + 8:  # ): line
        pass  # keep as is
    elif i == func_start + 9:  # docstring
        if leading == 2:
            lines[i] = '    ' + stripped
    else:  # function body
        if leading == 2:
            lines[i] = '    ' + stripped
        elif leading == 4:
            lines[i] = '    ' + stripped  # already 4, keep

# Now find and fix search_prices
start_found = False
func2_start = -1
func2_end = -1

for i, line in enumerate(lines):
    if '@router.get("/search", response_model=List[PriceUnitOut])' in line:
        func2_start = i
        start_found = True
    elif start_found and '@router.get("/topics"' in line:
        func2_end = i
        break

print(f"search_prices: lines {func2_start+1} to {func2_end+1}")

# Fix search_prices
for i in range(func2_start, func2_end):
    line = lines[i]
    stripped = line.lstrip()
    if not stripped:
        continue
    
    leading = len(line) - len(line.lstrip())
    
    # First 5 lines after decorator are params
    if i < func2_start + 6:  # param lines
        if leading == 2:
            lines[i] = '    ' + stripped
    elif i == func2_start + 6:  # ): line
        pass
    elif i == func2_start + 7:  # docstring
        if leading == 2:
            lines[i] = '    ' + stripped
    else:  # function body
        if leading == 2:
            lines[i] = '    ' + stripped

with open('packages/server/api/prices.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Done!')

# Verify
import py_compile
try:
    py_compile.compile('packages/server/api/prices.py', doraise=True)
    print('prices.py: OK')
except py_compile.PyCompileError as e:
    print(f'prices.py: ERROR - {e}')
