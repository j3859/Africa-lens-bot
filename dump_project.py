import os

output = []
output.append("# PROJECT STRUCTURE\n")

# Show folder structure
for root, dirs, files in os.walk("."):
    # Skip unwanted folders
    skip = ["venv", "__pycache__", "logs", ".git", "node_modules"]
    dirs[:] = [d for d in dirs if d not in skip]
    
    level = root.replace(".", "").count(os.sep)
    indent = "  " * level
    output.append(f"{indent}{os.path.basename(root)}/")
    
    for file in files:
        if not file.endswith((".pyc", ".log")):
            output.append(f"{indent}  {file}")

output.append("\n\n# FILE CONTENTS\n")

# Read each Python file
for root, dirs, files in os.walk("."):
    skip = ["venv", "__pycache__", "logs", ".git"]
    dirs[:] = [d for d in dirs if d not in skip]
    
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            output.append(f"\n{'='*60}")
            output.append(f"FILE: {filepath}")
            output.append("="*60)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    output.append(f.read())
            except:
                output.append("[Could not read file]")

# Write to file
with open("project_dump.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Created project_dump.txt")
print(f"Size: {os.path.getsize('project_dump.txt') / 1024:.1f} KB")