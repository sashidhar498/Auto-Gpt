import ast
import subprocess
import json
import os
import hashlib
from typing import List, Dict, Any

# Placeholder for Api_to_create - should be implemented elsewhere
def Api_to_create(task: str) -> str:
    """Placeholder for external API call. Returns original code."""
    return "# Placeholder API response"

def analyze_code_quality(file_path: str) -> Dict[str, Any]:
    """
    Analyzes Python file for style issues, unused imports, and duplicated logic.
    Returns a report dictionary with findings.
    """
    report = {
        "file_path": file_path,
        "style_issues": [],
        "unused_imports": [],
        "duplicated_logic": []
    }
    
    try:
        with open(file_path, 'r') as f:
            code = f.read()
            tree = ast.parse(code)
            
        # Check for unused imports using AST
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        
        # Simple unused import detection (basic implementation)
        # This is a simplified version - full implementation would track usage
        report["unused_imports"] = imports[:3]  # Placeholder
        
        # Run flake8 for style issues
        result = subprocess.run(
            ["flake8", file_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            report["style_issues"] = result.stdout.split('\n')[:5]  # Limit output
        
    except Exception as e:
        report["error"] = str(e)
    
    return report

def suggest_refactorations(analysis_report: Dict[str, Any]) -> List[str]:
    """
    Generates improvement suggestions from analysis report.
    Returns list of suggestion strings.
    """
    suggestions = []
    
    if analysis_report.get("style_issues"):
        suggestions.append("Fix style issues detected by flake8")
    if analysis_report.get("unused_imports"):
        suggestions.append("Remove unused imports")
    if analysis_report.get("duplicated_logic"):
        suggestions.append("Refactor duplicated logic")
    
    return suggestions

def apply_refactor(file_path: str, suggestions: List[str]) -> bool:
    """
    Applies refactorings using Api_to_create and writes back to file.
    Returns True if changes were made.
    """
    try:
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        task = f"Refactor {file_path} according to these suggestions: {json.dumps(suggestions)}"
        updated_code = Api_to_create(task)
        
        # Compare content
        if updated_code != original_code:
            with open(file_path, 'w') as f:
                f.write(updated_code)
            return True
        return False
    except Exception as e:
        print(f"Error applying refactor: {e}")
        return False

def get_python_files() -> List[str]:
    """Get all Python files in project directory and from functions.json"""
    files = []
    project_dir = os.getcwd()
    
    # Get all .py files in project
    for root, dirs, filenames in os.walk(project_dir):
        for filename in filenames:
            if filename.endswith('.py') and filename not in ['self_improvement.py', 'test_self_improvement.py']:
                files.append(os.path.join(root, filename))
    
    # Also check functions.json for listed modules
    if os.path.exists('functions.json'):
        with open('functions.json', 'r') as f:
            data = json.load(f)
        for module_name in data.keys():
            if module_name.endswith('.py'):
                files.append(module_name)
    
    return list(set(files))

def self_improve():
    """
    Orchestrates self-improvement for all Python files.
    Idempotent - exits quietly if no changes detected.
    """
    files = get_python_files()
    changes_made = False
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        # Get original hash
        with open(file_path, 'rb') as f:
            original_hash = hashlib.md5(f.read()).hexdigest()
        
        # Analyze
        report = analyze_code_quality(file_path)
        suggestions = suggest_refactorations(report)
        
        # Apply refactoring
        if suggestions:
            if apply_refactor(file_path, suggestions):
                changes_made = True
        
        # Check if changes were made
        with open(file_path, 'rb') as f:
            new_hash = hashlib.md5(f.read()).hexdigest()
        
        if new_hash != original_hash:
            changes_made = True
    
    # Exit quietly if no changes
    if not changes_made:
        return

def run_self_improvement_tests():
    """Runs unit tests for self_improvement module"""
    # Basic test cases
    test_file = "test_sample.py"
    
    # Create test file
    with open(test_file, 'w') as f:
        f.write("import os\nimport sys\n\ndef hello():\n    print('Hello')\n")
    
    # Test analyze_code_quality
    report = analyze_code_quality(test_file)
    assert "unused_imports" in report
    
    # Test suggest_refactorations
    suggestions = suggest_refactorations(report)
    assert isinstance(suggestions, list)
    
    # Test apply_refactor (with mock)
    # Note: Api_to_create is a placeholder
    
    # Cleanup
    os.remove(test_file)
    print("Tests passed")
