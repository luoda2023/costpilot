import py_compile
import os

# Check all server files for syntax errors
errors = []
for root, dirs, files in os.walk('packages/server'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))

if errors:
    for err in errors:
        print(f'ERROR: {err}')
else:
    print('All Python files OK')
