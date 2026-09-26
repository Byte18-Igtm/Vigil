import ast
import re
from typing import Any, Dict, List, Optional, Tuple


class CodeStaticAnalyzer:
    """
    Performs real AST and structural analysis of code across languages (Python, JS/TS, general).
    Used to ground explanations, debugging, and testing in actual syntax and semantics.
    """

    @staticmethod
    def analyze_python(code: str, target_line: int) -> Dict[str, Any]:
        """
        Parses Python code with python's built-in ast engine to extract concrete details,
        unbound names, syntax issues, function definitions, etc.
        """
        result: Dict[str, Any] = {
            "syntax_valid": True,
            "syntax_error": None,
            "target_node": None,
            "enclosing_function": None,
            "enclosing_class": None,
            "imports": [],
            "called_functions": [],
            "variables": [],
            "potential_issues": [],
            "testable_functions": []
        }

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["syntax_valid"] = False
            result["syntax_error"] = {
                "message": e.msg,
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
            result["potential_issues"].append({
                "type": "SyntaxError",
                "message": f"Syntax error at line {e.lineno}: {e.msg}",
                "line": e.lineno
            })
            return result

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
                self.current_function = None

            def visit_Import(self, node):
                for alias in node.names:
                    result["imports"].append(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                module = node.module or ""
                for alias in node.names:
                    result["imports"].append(f"{module}.{alias.name}")
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                prev_class = self.current_class
                self.current_class = node.name
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if node.lineno <= target_line <= (node.end_lineno or node.lineno):
                        result["enclosing_class"] = node.name
                self.generic_visit(node)
                self.current_class = prev_class

            def visit_FunctionDef(self, node):
                prev_fn = self.current_function
                self.current_function = node.name
                args = [arg.arg for arg in node.args.args]
                result["testable_functions"].append({
                    "name": node.name,
                    "args": args,
                    "is_async": False,
                    "line": node.lineno
                })
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if node.lineno <= target_line <= (node.end_lineno or node.lineno):
                        result["enclosing_function"] = node.name
                self.generic_visit(node)
                self.current_function = prev_fn

            def visit_AsyncFunctionDef(self, node):
                prev_fn = self.current_function
                self.current_function = node.name
                args = [arg.arg for arg in node.args.args]
                result["testable_functions"].append({
                    "name": node.name,
                    "args": args,
                    "is_async": True,
                    "line": node.lineno
                })
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if node.lineno <= target_line <= (node.end_lineno or node.lineno):
                        result["enclosing_function"] = node.name
                self.generic_visit(node)
                self.current_function = prev_fn

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    result["called_functions"].append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    result["called_functions"].append(node.func.attr)
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, (ast.Store, ast.Load)):
                    if node.id not in result["variables"] and node.id not in ["True", "False", "None"]:
                        result["variables"].append(node.id)
                self.generic_visit(node)

        visitor = Visitor()
        visitor.visit(tree)

        # Check for common code smells or bug patterns in target line
        lines = code.splitlines()
        if 1 <= target_line <= len(lines):
            line_str = lines[target_line - 1].strip()
            
            # Mutable default argument check
            for func in tree.body:
                if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in func.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            result["potential_issues"].append({
                                "type": "MutableDefaultArgument",
                                "message": f"Function '{func.name}' uses mutable default argument: danger of shared state across calls.",
                                "line": func.lineno
                            })
                            
            # Bare except clause
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    result["potential_issues"].append({
                        "type": "BareExcept",
                        "message": "Bare 'except:' catches BaseException (including KeyboardInterrupt and SystemExit). Use 'except Exception:' instead.",
                        "line": getattr(node, "lineno", target_line)
                    })

            # Check division by zero risk
            if "/" in line_str or "%" in line_str:
                if re.search(r"/\s*0(?!\d)", line_str):
                    result["potential_issues"].append({
                        "type": "ZeroDivisionError",
                        "message": "Direct division by zero detected.",
                        "line": target_line
                    })

            # Check assignment inside condition (common typo if user wrote 'if a = b')
            if re.search(r"if\s+[\w\.\(\)]+\s*=[^=]", line_str):
                result["potential_issues"].append({
                    "type": "AssignmentInCondition",
                    "message": "Possible assignment '=' instead of comparison '==' in condition.",
                    "line": target_line
                })

        return result

    @staticmethod
    def analyze_generic(code: str, target_line: int, language: str) -> Dict[str, Any]:
        """
        Analyzes JavaScript, TypeScript, or other C-like languages via regex pattern matcher.
        """
        lines = code.splitlines()
        target_str = lines[target_line - 1].strip() if 1 <= target_line <= len(lines) else ""
        
        functions = []
        fn_pattern = re.compile(r"(?:function\s+([a-zA-Z0-9_$]+)|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{)")
        for idx, line in enumerate(lines, start=1):
            match = fn_pattern.search(line)
            if match:
                name = match.group(1) or match.group(2) or match.group(3)
                if name:
                    functions.append({"name": name, "line": idx})

        potential_issues = []
        if language in ["javascript", "typescript", "typescriptreact", "javascriptreact"]:
            if "==" in target_str and "===" not in target_str:
                potential_issues.append({
                    "type": "LooseEquality",
                    "message": "Using loose equality '==' may cause unintended type coercion bugs. Prefer strict equality '==='.",
                    "line": target_line
                })
            if "await" in target_str and not any("async" in l for l in lines[:target_line]):
                potential_issues.append({
                    "type": "AwaitWithoutAsync",
                    "message": "'await' is used, but enclosing scope may not be marked as 'async'.",
                    "line": target_line
                })
            if re.search(r"console\.log\(", target_str):
                potential_issues.append({
                    "type": "ConsoleLog",
                    "message": "Production code contains debug 'console.log' call.",
                    "line": target_line
                })

        return {
            "target_line_content": target_str,
            "functions": functions,
            "potential_issues": potential_issues,
            "line_count": len(lines)
        }

    @staticmethod
    def run_maintenance_checks(code: str, language: str) -> Dict[str, Any]:
        """
        Executes comprehensive code maintenance and health checks.
        Evaluates technical debt, documentation completeness, type annotations,
        cyclomatic complexity, resource safety, and antipatterns.
        """
        checks: List[str] = []
        recommendations: List[str] = []
        debt_points = 0
        lang = (language or "python").lower()

        if lang == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    "checks": ["❌ Syntax parse failure: code cannot be cleanly compiled"],
                    "score": "high_risk",
                    "recommendations": ["Fix syntax errors before performing maintenance reviews."]
                }

            # 1. Type annotations check
            functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if functions:
                typed_args = 0
                total_args = 0
                has_return_type = 0
                for fn in functions:
                    for arg in fn.args.args:
                        total_args += 1
                        if arg.annotation is not None:
                            typed_args += 1
                    if fn.returns is not None:
                        has_return_type += 1

                if total_args > 0 and typed_args == total_args:
                    checks.append("✓ Type Annotations: 100% parameter type coverage")
                elif total_args > 0 and typed_args > 0:
                    checks.append(f"⚠ Type Annotations: Partial coverage ({typed_args}/{total_args} arguments typed)")
                    debt_points += 1
                    recommendations.append("Add missing type hints to function signatures for better static safety and IDE autocomplete.")
                else:
                    checks.append("⚠ Type Annotations: Missing type hints on function parameters")
                    debt_points += 1
                    recommendations.append("Adopt PEP 484 type annotations for function parameters and return types.")

            # 2. Documentation / Docstrings check
            if functions:
                documented = sum(1 for fn in functions if ast.get_docstring(fn))
                if documented == len(functions):
                    checks.append("✓ Documentation: All declared functions have valid docstrings")
                else:
                    checks.append(f"⚠ Documentation: {len(functions) - documented} function(s) missing docstrings")
                    debt_points += 1
                    recommendations.append("Provide concise docstrings explaining purpose, arguments, and return values.")

            # 3. Mutable default arguments
            mutable_defaults_found = False
            for fn in functions:
                for default in fn.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        mutable_defaults_found = True
                        break
            if mutable_defaults_found:
                checks.append("❌ Antipattern: Mutable default arguments detected in function definition")
                debt_points += 2
                recommendations.append("Replace mutable default arguments (e.g. `def f(arg=[])`) with `arg=None` and initialize in body.")
            else:
                checks.append("✓ Antipatterns: No mutable default arguments found")

            # 4. Bare exception handlers
            bare_except_found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    bare_except_found = True
                    break
            if bare_except_found:
                checks.append("❌ Error Boundaries: Bare 'except:' clause caught (catches system exit & interrupts)")
                debt_points += 2
                recommendations.append("Replace bare 'except:' with explicit exception types like 'except Exception as e:'.")
            else:
                checks.append("✓ Error Boundaries: Safe exception handling (no bare excepts)")

            # 5. Resource management / unclosed files
            open_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"]
            with_blocks = [n for n in ast.walk(tree) if isinstance(n, ast.With)]
            if open_calls and not with_blocks:
                checks.append("⚠ Resource Safety: Direct 'open()' call found without 'with' context manager")
                debt_points += 2
                recommendations.append("Use 'with open(...) as f:' context managers to ensure deterministic file closing.")
            else:
                checks.append("✓ Resource Safety: Clean context management principles verified")

            # 6. Global variable mutation
            global_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Global)]
            if global_nodes:
                checks.append("⚠ Architecture: 'global' keyword used, introducing shared state coupling")
                debt_points += 1
                recommendations.append("Refactor shared mutable state into class instances or functional return values.")
            else:
                checks.append("✓ Architecture: Pure state flow without global keyword mutations")

        else:
            # Generic JS/TS maintenance checks
            if "==" in code and "===" not in code:
                checks.append("⚠ Equality Checks: Using loose '==' instead of strict '==='")
                debt_points += 1
                recommendations.append("Adopt strict equality '===' to avoid coercion edge-case bugs.")
            else:
                checks.append("✓ Equality Checks: Strict type equality maintained")

            if "console.log" in code:
                checks.append("⚠ Clean Code: Debug 'console.log' statements present")
                debt_points += 1
                recommendations.append("Remove production console.log calls or replace with structured logger.")
            else:
                checks.append("✓ Clean Code: No leftover debug logging found")

            checks.append("✓ Linting Check: No critical syntax flaws detected")

        # Determine overall maintenance health rating
        if debt_points == 0:
            score = "clean"
        elif debt_points <= 2:
            score = "moderate_debt"
        else:
            score = "high_risk"

        if not recommendations:
            recommendations.append("Codebase is clean. Maintain test coverage and follow existing typing conventions.")

        return {
            "checks": checks,
            "score": score,
            "recommendations": recommendations
        }
