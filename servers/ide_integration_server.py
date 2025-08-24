#!/usr/bin/env python3
"""
IDE Integration Server (Port 8004)
Provides integration with development environments and code analysis
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ast
import re
import shutil
import asyncio

from logging_config import setup_logger, ServiceMonitor

# Configure logging
logger = setup_logger("ide_integration_server")

app = FastAPI(title="IDE Integration Server", version="1.0.0")

# Initialize ServiceMonitor
monitor = ServiceMonitor("ide_integration_server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeAnalysis(BaseModel):
    file_path: str
    content: str
    language: str

class CodeSuggestion(BaseModel):
    line: int
    message: str
    severity: str
    suggestion: Optional[str] = None

class CodeFormat(BaseModel):
    content: str
    language: str

class CodeRefactor(BaseModel):
    content: str
    language: str
    old_name: str
    new_name: str

class CodeCompletion(BaseModel):
    content: str
    language: str
    line: int
    column: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    supported_languages: List[str]
    active_sessions: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for IDE integration server"""
    monitor.record_request()
    monitor.record_success()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        supported_languages=["python", "javascript", "typescript", "go", "rust", "java", "cpp"],
        active_sessions=0  # Would track active IDE sessions
    )

@app.post("/analyze/code")
async def analyze_code(analysis: CodeAnalysis):
    """Analyze code for issues, patterns, and suggestions"""
    monitor.record_request()
    try:
        issues = []
        
        if analysis.language.lower() == "python":
            issues = await analyze_python_code(analysis.content)
        elif analysis.language.lower() in ["javascript", "typescript"]:
            issues = await analyze_javascript_code(analysis.content)
        elif analysis.language.lower() == "go":
            issues = await analyze_go_code(analysis.content)
        else:
            issues = await analyze_generic_code(analysis.content)
        
        monitor.record_success()
        return {
            "file_path": analysis.file_path,
            "language": analysis.language,
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "errors": len([i for i in issues if i["severity"] == "error"]),
                "warnings": len([i for i in issues if i["severity"] == "warning"]),
                "info": len([i for i in issues if i["severity"] == "info"])
            }
        }
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/format/code")
async def format_code(code_format: CodeFormat):
    """Format code using language-specific formatters"""
    monitor.record_request()
    try:
        formatted_content = code_format.content
        if code_format.language.lower() == "python":
            if shutil.which("black"):
                process = await asyncio.create_subprocess_shell(
                    "black -q - ",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate(input=code_format.content.encode())
                if process.returncode == 0:
                    formatted_content = stdout.decode()
                    monitor.record_success()
                else:
                    monitor.record_error(f"Black formatting failed: {stderr.decode()}")
                    logger.error(f"Black formatting failed: {stderr.decode()}")
                    raise HTTPException(status_code=500, detail=f"Black formatting failed: {stderr.decode()}")
            else:
                monitor.record_error("Black is not installed")
                raise HTTPException(status_code=500, detail="Black is not installed. Please install it: pip install black")
        elif code_format.language.lower() in ["javascript", "typescript"]:
            if shutil.which("prettier"):
                process = await asyncio.create_subprocess_shell(
                    "prettier --stdin --parser typescript", # Use typescript parser for both js/ts
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate(input=code_format.content.encode())
                if process.returncode == 0:
                    formatted_content = stdout.decode()
                    monitor.record_success()
                else:
                    monitor.record_error(f"Prettier formatting failed: {stderr.decode()}")
                    logger.error(f"Prettier formatting failed: {stderr.decode()}")
                    raise HTTPException(status_code=500, detail=f"Prettier formatting failed: {stderr.decode()}")
            else:
                monitor.record_error("Prettier is not installed")
                raise HTTPException(status_code=500, detail="Prettier is not installed. Please install it: npm install -g prettier")
        elif code_format.language.lower() == "go":
            if shutil.which("gofmt"):
                process = await asyncio.create_subprocess_shell(
                    "gofmt",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate(input=code_format.content.encode())
                if process.returncode == 0:
                    formatted_content = stdout.decode()
                    monitor.record_success()
                else:
                    monitor.record_error(f"Gofmt formatting failed: {stderr.decode()}")
                    logger.error(f"Gofmt formatting failed: {stderr.decode()}")
                    raise HTTPException(status_code=500, detail=f"Gofmt formatting failed: {stderr.decode()}")
            else:
                monitor.record_error("Gofmt is not installed")
                raise HTTPException(status_code=500, detail="Gofmt is not installed. Please install Go and ensure gofmt is in your PATH.")
        else:
            monitor.record_error(f"Formatting not supported for language: {code_format.language}")
            raise HTTPException(status_code=400, detail=f"Formatting not supported for language: {code_format.language}")
        
        return {"formatted_content": formatted_content}
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Code formatting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refactor/rename")
async def refactor_rename(refactor: CodeRefactor):
    """Perform a simple rename refactoring within the code content"""
    monitor.record_request()
    try:
        # This is a basic string replacement. For true refactoring, a language server would be needed.
        new_content = refactor.content.replace(refactor.old_name, refactor.new_name)
        monitor.record_success()
        return {"refactored_content": new_content}
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Refactoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_python_code(content: str) -> List[Dict[str, Any]]:
    """Analyze Python code for common issues"""
    issues = []
    
    try:
        tree = ast.parse(content)
        
        # Check for unused imports and variables
        defined_names = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    defined_names.add(alias.asname or alias.name)
        
        unused_symbols = defined_names - used_names
        for symbol in unused_symbols:
            issues.append({
                "line": 0, # Cannot easily get line number for unused symbols from AST without more complex logic
                "message": f"Unused symbol: {symbol}",
                "severity": "warning",
                "suggestion": "Remove unused symbol"
            })

        # Check for basic Python issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for print statements
            if re.search(r'\bprint\s*\(', line_stripped):
                issues.append({
                    "line": i,
                    "message": "Consider using logging instead of print",
                    "severity": "info",
                    "suggestion": "Use logging.info() or appropriate logging level"
                })
            
            # Check for bare except
            if re.search(r'except\s*:', line_stripped):
                issues.append({
                    "line": i,
                    "message": "Avoid bare except clauses",
                    "severity": "warning",
                    "suggestion": "Catch specific exceptions"
                })
            
            # Check for TODO comments
            if re.search(r'\bTODO\b|\bFIXME\b|\bXXX\b', line_stripped, re.IGNORECASE):
                issues.append({
                    "line": i,
                    "message": "Pending task found",
                    "severity": "info",
                    "suggestion": "Address TODO/FIXME comments"
                })
    
    except SyntaxError as e:
        issues.append({
            "line": e.lineno or 1,
            "message": f"Syntax error: {e.msg}",
            "severity": "error",
            "suggestion": "Fix syntax error"
        })
    
    return issues

async def analyze_javascript_code(content: str) -> List[Dict[str, Any]]:
    """Analyze JavaScript/TypeScript code"""
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Check for console.log statements
        if re.search(r'\bconsole\\.log\s*\(', line_stripped):
            issues.append({
                "line": i,
                "message": "Consider removing console.log statements",
                "severity": "info",
                "suggestion": "Use proper logging or remove debug statements"
            })
        
        # Check for var usage
        if re.search(r'\bvar\s+\w+\s*=', line_stripped):
            issues.append({
                "line": i,
                "message": "Use let or const instead of var",
                "severity": "warning",
                "suggestion": "Replace var with let or const"
            })
        
        # Check for unused variables (basic - very rudimentary, needs AST for accuracy)
        # This regex is too broad and will likely produce false positives
        # if re.search(r'\blet\s+\w+\s*;', line_stripped) or re.search(r'\bconst\s+\w+\s*;', line_stripped):
        #     issues.append({
        #         "line": i,
        #         "message": "Unused variable declaration",
        #         "severity": "info",
        #         "suggestion": "Remove unused variable or use it"
        #     })

        # Check for loose equality (== instead of ===)
        if re.search(r'[^=]==[^=]', line_stripped):
            issues.append({
                "line": i,
                "message": "Consider using strict equality (===) instead of (==)",
                "severity": "warning",
                "suggestion": "Use === for comparison"
            })

        # Check for missing semicolons (basic - can be complex with ASI)
        if not line_stripped.endswith((';', '{', '}', ')', ']', 'else')) and line_stripped != '' and not line_stripped.startswith(('import', 'export', '//', '/*')):
            # Heuristic to avoid false positives on control structures, function definitions, etc.
            if not (re.match(r'^(if|for|while|switch|function|class)\b', line_stripped) or \
                    re.match(r'^\w+\s*\([^)]*\)\s*\{', line_stripped) or \
                    re.match(r'^\s*\}', line_stripped)):
                issues.append({
                    "line": i,
                    "message": "Missing semicolon",
                    "severity": "info",
                    "suggestion": "Add a semicolon at the end of the statement"
                })
    
    return issues

async def analyze_go_code(content: str) -> List[Dict[str, Any]]:
    """Analyze Go code"""
    issues = []
    lines = content.split('\n')
    
    # Basic check for unused imports (requires more sophisticated parsing for accuracy)
    imported_packages = set(re.findall(r'import\s*(?:"([^"]+)"|\(([^)]+)\))', content))
    # Flatten the set of tuples/strings
    flat_imports = set()
    for imp in imported_packages:
        if isinstance(imp, tuple):
            for item in imp:
                if item:
                    flat_imports.add(item.strip())
        else:
            if imp:
                flat_imports.add(imp.strip())

    for imp in flat_imports:
        # Very basic check: if package name is not found in content, it might be unused
        package_name = imp.split('/')[-1]
        if package_name and f'{package_name}.' not in content and f' {package_name} ' not in content:
            issues.append({
                "line": 0, # Cannot easily determine line number for imports without proper AST for Go
                "message": f"Potentially unused import: {imp}",
                "severity": "warning",
                "suggestion": "Remove unused import"
            })

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Check for error handling
        if re.search(r'\bif\s+err\s*!=\s*nil\s*\{', line_stripped):
            # This is a common pattern, but could be enhanced to check for proper error handling
            pass

        # Check for unused variables (very basic, needs AST for accuracy)
        # Go compiler usually catches this, but for a linter, we can add a heuristic
        if re.search(r'\bvar\s+\w+\s*[^=]*$', line_stripped) or re.search(r':=\s*[^,]+$', line_stripped):
            var_name_match = re.search(r'\b(var\s+(\w+)|(\w+)\s*:=)', line_stripped)
            if var_name_match:
                var_name = var_name_match.group(2) or var_name_match.group(3)
                # Check if the variable is used later in the same function/scope (very hard with regex)
                # This is a placeholder for a more robust check
                if f' {var_name}' not in content[content.find(line):] and f'{var_name}.' not in content[content.find(line):]:
                     issues.append({
                        "line": i,
                        "message": f"Potentially unused variable: {var_name}",
                        "severity": "warning",
                        "suggestion": "Remove unused variable or use it"
                    })

    return issues

async def analyze_generic_code(content: str) -> List[Dict[str, Any]]:
    """Analyze generic code for common issues (e.g., TODOs) without language-specific parsing"""
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if re.search(r'\bTODO\b|\bFIXME\b|\bXXX\b', line_stripped, re.IGNORECASE):
            issues.append({
                "line": i,
                "message": "Pending task found",
                "severity": "info",
                "suggestion": "Address TODO/FIXME comments"
            })
    return issues

@app.post("/lint/code")
async def lint_code(analysis: CodeAnalysis):
    """Lint code using language-specific linters"""
    try:
        lint_output = ""
        if analysis.language.lower() == "python":
            if shutil.which("pylint"):
                process = await asyncio.create_subprocess_shell(
                    "pylint --from-stdin " + analysis.file_path, # pylint needs a filename for some checks
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate(input=analysis.content.encode())
                lint_output = stdout.decode() + stderr.decode()
            else:
                raise HTTPException(status_code=500, detail="Pylint is not installed. Please install it: pip install pylint")
        elif analysis.language.lower() in ["javascript", "typescript"]:
            if shutil.which("eslint"):
                # ESLint typically needs a config file and actual files on disk. This is a simplified approach.
                # For a real-world scenario, you'd write content to a temp file and run eslint on it.
                temp_file_path = f"/tmp/temp_lint_file.{'ts' if analysis.language.lower() == 'typescript' else 'js'}"
                with open(temp_file_path, "w") as f:
                    f.write(analysis.content)
                process = await asyncio.create_subprocess_shell(
                    f"eslint {temp_file_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                lint_output = stdout.decode() + stderr.decode()
                os.remove(temp_file_path)
            else:
                raise HTTPException(status_code=500, detail="ESLint is not installed. Please install it: npm install -g eslint")
        elif analysis.language.lower() == "go":
            if shutil.which("golint"):
                # golint also typically works on files. Similar temp file approach.
                temp_file_path = "/tmp/temp_lint_file.go"
                with open(temp_file_path, "w") as f:
                    f.write(analysis.content)
                process = await asyncio.create_subprocess_shell(
                    f"golint {temp_file_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                lint_output = stdout.decode() + stderr.decode()
                os.remove(temp_file_path)
            else:
                raise HTTPException(status_code=500, detail="Golint is not installed. Please install it: go get -u golang.org/x/lint/golint")
        else:
            raise HTTPException(status_code=400, detail=f"Linting not supported for language: {analysis.language}")
        
        return {"lint_output": lint_output}
    except Exception as e:
        logger.error(f"Code linting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autocomplete")
async def autocomplete(completion: CodeCompletion):
    """Provide basic code completion suggestions"""
    try:
        suggestions = []
        # This is a very basic example. A real autocomplete would use a language server.
        keywords = {
            "python": ["def", "class", "import", "from", "if", "else", "for", "while", "return", "True", "False", "None"],
            "javascript": ["function", "const", "let", "var", "import", "export", "if", "else", "for", "while", "return", "true", "false", "null"],
            "go": ["func", "package", "import", "var", "const", "if", "else", "for", "return", "true", "false", "nil"]
        }

        current_line = completion.content.split('\n')[completion.line - 1]
        prefix = current_line[:completion.column]

        lang_keywords = keywords.get(completion.language.lower(), [])
        for keyword in lang_keywords:
            if keyword.startswith(prefix):
                suggestions.append(keyword)
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/breakpoint")
async def set_breakpoint(file_path: str, line_number: int, enable: bool = True):
    """Set or clear a breakpoint in a file (placeholder)"""
    logger.info(f"Breakpoint {'set' if enable else 'cleared'} at {file_path}:{line_number}")
    return {"status": "success", "message": f"Breakpoint {'set' if enable else 'cleared'} at {file_path}:{line_number}"}

@app.post("/test/run")
async def run_tests(file_path: Optional[str] = None, test_name: Optional[str] = None, language: str = "python"):
    """Run tests for a given file or test name (placeholder)"""
    logger.info(f"Running tests for {file_path or 'all'} (test: {test_name or 'all'}) in {language}")
    return {"status": "success", "message": "Test execution initiated (placeholder)"}

async def analyze_generic_code(content: str) -> List[Dict[str, Any]]:
    """Analyze generic code for common issues (e.g., TODOs) without language-specific parsing"""
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if re.search(r'\bTODO\b|\bFIXME\b|\bXXX\b', line_stripped, re.IGNORECASE):
            issues.append({
                "line": i,
                "message": "Pending task found",
                "severity": "info",
                "suggestion": "Address TODO/FIXME comments"
            })
    return issues

@app.get("/project/structure/{path:path}")
async def get_project_structure(path: str):
    """Get project file structure"""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="Path not found")
        
        def build_tree(current_path, max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return None
            
            tree = {}
            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    if os.path.isdir(item_path):
                        subtree = build_tree(item_path, max_depth, current_depth + 1)
                        if subtree:
                            tree[item] = subtree
                        else:
                            tree[item] = "directory"
                    else:
                        tree[item] = "file"
            except PermissionError:
                tree["<permission_denied>"] = "error"
            
            return tree
        
        structure = build_tree(abs_path)
        return {
            "path": abs_path,
            "structure": structure,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to get project structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/git/diff")
async def get_git_diff(file_path: str):
    """Get git diff for a specific file"""
    try:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if in git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=os.path.dirname(abs_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {"diff": "Not in a git repository"}
        
        # Get git diff
        result = subprocess.run(
            ["git", "diff", abs_path],
            cwd=os.path.dirname(abs_path),
            capture_output=True,
            text=True
        )
        
        return {
            "file_path": abs_path,
            "diff": result.stdout,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Git diff failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)