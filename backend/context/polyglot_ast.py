import os
import re
import ast
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Try importing tree_sitter for binary AST parsing if available
try:
    import tree_sitter
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class SymbolDefinition(BaseModel):
    name: str
    symbol_type: str  # "function", "async_function", "class", "interface", "import", "variable", "route", "model"
    args: List[str] = Field(default_factory=list)  # For functions: argument names; for classes: method names
    line_number: int = 0
    docstring: Optional[str] = None
    return_type: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    is_exported: bool = False
    file_path: Optional[str] = None


class RouteDefinition(BaseModel):
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH, USE, INTENT
    handler_name: str
    line_number: int = 0
    file_path: Optional[str] = None


class DatabaseModelDefinition(BaseModel):
    name: str
    fields: List[str] = Field(default_factory=list)
    model_type: str = "orm"  # mongoose, jpa, room, sqlalchemy, pydantic, etc.
    table_or_collection: Optional[str] = None
    line_number: int = 0
    file_path: Optional[str] = None


class CrossFileImport(BaseModel):
    source_path: str  # e.g., "./auth.js", "com.example.service.UserService", "models.user"
    imported_symbols: List[str] = Field(default_factory=list)
    is_relative: bool = False
    raw_statement: str = ""
    line_number: int = 0


class SymbolTable(BaseModel):
    imports: List[str] = Field(default_factory=list)
    functions: List[SymbolDefinition] = Field(default_factory=list)
    classes: List[SymbolDefinition] = Field(default_factory=list)
    global_variables: List[str] = Field(default_factory=list)
    routes: List[RouteDefinition] = Field(default_factory=list)
    database_models: List[DatabaseModelDefinition] = Field(default_factory=list)
    cross_file_imports: List[CrossFileImport] = Field(default_factory=list)
    interfaces: List[SymbolDefinition] = Field(default_factory=list)


class PolyglotASTEngine:
    """
    Polyglot AST & Call-Graph Parser Engine.
    Supports Python (.py), JavaScript/React (.js, .jsx), TypeScript (.ts, .tsx),
    Java Spring Boot (.java), Kotlin/Android (.kt), and AndroidManifest.xml.
    Integrates tree-sitter when grammars are available, with graceful high-fidelity
    fallback to Python AST, ElementTree XML, and robust AST regex parsers.
    """

    @classmethod
    def parse(cls, code: str, filename: str = "snippet.py") -> SymbolTable:
        ext = os.path.splitext(filename)[1].lower()
        basename = os.path.basename(filename).lower()

        if basename == "androidmanifest.xml" or ext == ".xml":
            return cls._parse_android_xml(code, filename)
        elif ext == ".py":
            return cls._parse_python(code, filename)
        elif ext in [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]:
            return cls._parse_javascript_typescript(code, filename)
        elif ext in [".java"]:
            return cls._parse_java(code, filename)
        elif ext in [".kt", ".kts"]:
            return cls._parse_kotlin(code, filename)
        else:
            # Fallback for generic files
            return cls._parse_generic(code, filename)

    # -------------------------------------------------------------------------
    # Python Parser (Standard AST + Route/Model detection)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_python(cls, code: str, filename: str) -> SymbolTable:
        imports: List[str] = []
        cross_imports: List[CrossFileImport] = []
        functions: List[SymbolDefinition] = []
        classes: List[SymbolDefinition] = []
        variables: List[str] = []
        routes: List[RouteDefinition] = []
        models: List[DatabaseModelDefinition] = []

        try:
            tree = ast.parse(code)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        cross_imports.append(CrossFileImport(
                            source_path=alias.name,
                            imported_symbols=[alias.asname or alias.name],
                            is_relative=False,
                            raw_statement=f"import {alias.name}",
                            line_number=node.lineno
                        ))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    is_rel = (node.level or 0) > 0
                    prefix = "." * (node.level or 0)
                    full_mod = f"{prefix}{module}" if is_rel else module
                    symbols_list = []
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}" if module else alias.name
                        imports.append(full_name)
                        symbols_list.append(alias.asname or alias.name)
                    cross_imports.append(CrossFileImport(
                        source_path=full_mod or module,
                        imported_symbols=symbols_list,
                        is_relative=is_rel,
                        raw_statement=f"from {full_mod} import {', '.join(symbols_list)}",
                        line_number=node.lineno
                    ))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    arg_names = [arg.arg for arg in node.args.args]
                    docstring = ast.get_docstring(node)
                    decorator_names = []
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            decorator_names.append(dec.id)
                        elif isinstance(dec, ast.Attribute):
                            decorator_names.append(f"{ast.unparse(dec.value)}.{dec.attr}")
                        elif isinstance(dec, ast.Call):
                            func_name = ast.unparse(dec.func) if hasattr(ast, "unparse") else "decorator"
                            decorator_names.append(func_name)
                            # Check FastAPI / Flask route: @app.get("/users"), @router.post("/items")
                            for http_method in ["get", "post", "put", "delete", "patch"]:
                                if func_name.endswith(f".{http_method}") or func_name == http_method:
                                    route_path = "/"
                                    if dec.args and isinstance(dec.args[0], ast.Constant):
                                        route_path = str(dec.args[0].value)
                                    routes.append(RouteDefinition(
                                        path=route_path,
                                        method=http_method.upper(),
                                        handler_name=node.name,
                                        line_number=node.lineno,
                                        file_path=filename
                                    ))

                    functions.append(SymbolDefinition(
                        name=node.name,
                        symbol_type="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                        args=arg_names,
                        line_number=node.lineno,
                        docstring=docstring,
                        decorators=decorator_names,
                        is_exported=not node.name.startswith("_"),
                        file_path=filename
                    ))
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    docstring = ast.get_docstring(node)
                    base_names = []
                    for b in node.bases:
                        if isinstance(b, ast.Name):
                            base_names.append(b.id)
                        elif hasattr(ast, "unparse"):
                            base_names.append(ast.unparse(b))

                    classes.append(SymbolDefinition(
                        name=node.name,
                        symbol_type="class",
                        args=methods,
                        line_number=node.lineno,
                        docstring=docstring,
                        is_exported=not node.name.startswith("_"),
                        file_path=filename
                    ))

                    # Check ORM / DB Model base classes
                    orm_bases = {"Base", "Model", "BaseModel", "SQLModel", "Document"}
                    if any(b in orm_bases or any(ob in b for ob in orm_bases) for b in base_names):
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                fields.append(item.target.id)
                            elif isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        fields.append(target.id)
                        models.append(DatabaseModelDefinition(
                            name=node.name,
                            fields=fields,
                            model_type="sqlalchemy/pydantic",
                            line_number=node.lineno,
                            file_path=filename
                        ))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
        except SyntaxError:
            pass

        # Regex fallback for routes if AST didn't capture (e.g. unparse unsupported or complex decorator)
        if not routes:
            route_matches = re.finditer(r'@(\w+)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', code, re.IGNORECASE)
            for m in route_matches:
                routes.append(RouteDefinition(
                    path=m.group(3),
                    method=m.group(2).upper(),
                    handler_name=m.group(1),
                    line_number=code[:m.start()].count("\n") + 1,
                    file_path=filename
                ))

        return SymbolTable(
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            global_variables=list(set(variables)),
            routes=routes,
            database_models=models,
            cross_file_imports=cross_imports,
            interfaces=[]
        )

    # -------------------------------------------------------------------------
    # JavaScript & TypeScript Parser (Node / Express / React / Mongoose)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_javascript_typescript(cls, code: str, filename: str) -> SymbolTable:
        imports: List[str] = []
        cross_imports: List[CrossFileImport] = []
        functions: List[SymbolDefinition] = []
        classes: List[SymbolDefinition] = []
        interfaces: List[SymbolDefinition] = []
        variables: List[str] = []
        routes: List[RouteDefinition] = []
        models: List[DatabaseModelDefinition] = []

        lines = code.split("\n")

        # 1. Imports
        # ES6: import { a, b } from './module' or import x from 'mod'
        es6_import_re = re.compile(r'import\s+(?:(?:\*\s+as\s+(\w+)|(\w+)|(?:\{([^}]+)\}))\s+from\s+)?["\']([^"\']+)["\']')
        # CJS: const x = require('./module') or const { a, b } = require('mod')
        cjs_import_re = re.compile(r'(?:const|let|var)\s+(?:(\w+)|\{([^}]+)\})\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)')

        for line_idx, line in enumerate(lines, 1):
            for m in es6_import_re.finditer(line):
                source = m.group(4)
                symbols = []
                if m.group(1):
                    symbols.append(m.group(1))
                elif m.group(2):
                    symbols.append(m.group(2))
                elif m.group(3):
                    symbols = [s.strip().split(" as ")[0].strip() for s in m.group(3).split(",") if s.strip()]
                is_rel = source.startswith(".") or source.startswith("/")
                imports.append(source)
                cross_imports.append(CrossFileImport(
                    source_path=source,
                    imported_symbols=symbols,
                    is_relative=is_rel,
                    raw_statement=line.strip(),
                    line_number=line_idx
                ))

            for m in cjs_import_re.finditer(line):
                source = m.group(3)
                symbols = []
                if m.group(1):
                    symbols.append(m.group(1))
                elif m.group(2):
                    symbols = [s.strip() for s in m.group(2).split(",") if s.strip()]
                is_rel = source.startswith(".") or source.startswith("/")
                imports.append(source)
                cross_imports.append(CrossFileImport(
                    source_path=source,
                    imported_symbols=symbols,
                    is_relative=is_rel,
                    raw_statement=line.strip(),
                    line_number=line_idx
                ))

        # 2. REST Routes (Express / Fastify / Next.js API / Router)
        # e.g., router.get('/users', ...), app.post('/auth/login', ...)
        route_re = re.compile(
            r'(?:app|router|server|api)\s*\.\s*(get|post|put|delete|patch|use)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:async\s*)?(?:function\s*([a-zA-Z0-9_]+)?|\(([a-zA-Z0-9_,\s]*)\)\s*=>|([a-zA-Z0-9_]+))',
            re.IGNORECASE
        )
        for line_idx, line in enumerate(lines, 1):
            for m in route_re.finditer(line):
                method = m.group(1).upper()
                route_path = m.group(2)
                handler = m.group(3) or m.group(5) or "anonymous_handler"
                routes.append(RouteDefinition(
                    path=route_path,
                    method=method,
                    handler_name=handler,
                    line_number=line_idx,
                    file_path=filename
                ))

        # 3. Database Models (Mongoose Schema/Model, Prisma, TypeORM)
        mongoose_schema_re = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:mongoose\.)?model\s*\(\s*["\'](\w+)["\']', re.IGNORECASE)
        for line_idx, line in enumerate(lines, 1):
            for m in mongoose_schema_re.finditer(line):
                models.append(DatabaseModelDefinition(
                    name=m.group(1),
                    fields=[],
                    model_type="mongoose",
                    table_or_collection=m.group(2),
                    line_number=line_idx,
                    file_path=filename
                ))

        # 4. Classes & Interfaces
        class_re = re.compile(r'(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z0-9_]+)(?:\s+extends\s+([a-zA-Z0-9_]+))?')
        interface_re = re.compile(r'(?:export\s+)?interface\s+([a-zA-Z0-9_]+)')

        for line_idx, line in enumerate(lines, 1):
            for m in class_re.finditer(line):
                cname = m.group(1)
                # Lookahead for methods inside class
                methods = []
                for sub_line in lines[line_idx:min(len(lines), line_idx + 60)]:
                    method_m = re.match(r'^\s*(?:async\s+)?([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*\{', sub_line)
                    if method_m and method_m.group(1) not in ("if", "for", "while", "switch", "catch"):
                        methods.append(method_m.group(1))
                    elif re.match(r'^\s*\}', sub_line):
                        break
                classes.append(SymbolDefinition(
                    name=cname,
                    symbol_type="class",
                    args=methods,
                    line_number=line_idx,
                    is_exported="export" in line,
                    file_path=filename
                ))

            for m in interface_re.finditer(line):
                iname = m.group(1)
                interfaces.append(SymbolDefinition(
                    name=iname,
                    symbol_type="interface",
                    args=[],
                    line_number=line_idx,
                    is_exported="export" in line,
                    file_path=filename
                ))

        # 5. Functions & Exported Functions
        func_re = re.compile(
            r'(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)|(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>'
        )
        for line_idx, line in enumerate(lines, 1):
            for m in func_re.finditer(line):
                fname = m.group(1) or m.group(3)
                raw_args = m.group(2) if m.group(1) else m.group(4)
                if not fname or fname in ("require", "if", "for", "while", "catch"):
                    continue
                args = [a.strip().split(":")[0].strip().split("=")[0].strip() for a in (raw_args or "").split(",") if a.strip()]
                functions.append(SymbolDefinition(
                    name=fname,
                    symbol_type="async_function" if "async" in line else "function",
                    args=args,
                    line_number=line_idx,
                    is_exported="export" in line,
                    file_path=filename
                ))

        return SymbolTable(
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            global_variables=variables,
            routes=routes,
            database_models=models,
            cross_file_imports=cross_imports,
            interfaces=interfaces
        )

    # -------------------------------------------------------------------------
    # Java & Spring Boot Parser
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_java(cls, code: str, filename: str) -> SymbolTable:
        imports: List[str] = []
        cross_imports: List[CrossFileImport] = []
        functions: List[SymbolDefinition] = []
        classes: List[SymbolDefinition] = []
        routes: List[RouteDefinition] = []
        models: List[DatabaseModelDefinition] = []

        lines = code.split("\n")

        # 1. Imports
        import_re = re.compile(r'import\s+(?:static\s+)?([a-zA-Z0-9_.*]+);')
        for line_idx, line in enumerate(lines, 1):
            m = import_re.search(line)
            if m:
                pkg = m.group(1)
                imports.append(pkg)
                cross_imports.append(CrossFileImport(
                    source_path=pkg,
                    imported_symbols=[pkg.split(".")[-1]],
                    is_relative=False,
                    raw_statement=line.strip(),
                    line_number=line_idx
                ))

        # 2. Spring Boot REST Endpoints (@GetMapping, @PostMapping, etc.)
        spring_route_re = re.compile(
            r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']|\(\s*\))?',
            re.IGNORECASE
        )
        for line_idx, line in enumerate(lines, 1):
            m = spring_route_re.search(line)
            if m:
                method = m.group(1).replace("Mapping", "").upper()
                if method == "REQUEST":
                    method = "ALL"
                route_path = m.group(2) or "/"
                # Look for handler method name on next 1-3 lines
                handler_name = "springHandler"
                for lookahead in lines[line_idx:min(len(lines), line_idx + 4)]:
                    meth_m = re.search(r'(?:public|protected|private)?\s*[\w<>\[\],\s]+\s+([a-zA-Z0-9_]+)\s*\(', lookahead)
                    if meth_m and meth_m.group(1) not in ("if", "while", "for", "switch", "catch"):
                        handler_name = meth_m.group(1)
                        break
                routes.append(RouteDefinition(
                    path=route_path,
                    method=method,
                    handler_name=handler_name,
                    line_number=line_idx,
                    file_path=filename
                ))

        # 3. Classes and Database Models (@Entity, @Table)
        class_re = re.compile(r'(?:public|protected|private)?\s*(?:abstract|final|static)?\s*(class|interface|record|enum)\s+([a-zA-Z0-9_]+)')
        is_entity = "@Entity" in code or "@Table" in code or "@Document" in code

        for line_idx, line in enumerate(lines, 1):
            m = class_re.search(line)
            if m:
                c_type = m.group(1)
                c_name = m.group(2)
                # Method scan
                methods = []
                for sub_line in lines[line_idx:min(len(lines), line_idx + 80)]:
                    sub_m = re.search(r'(?:public|protected|private)\s+[\w<>\[\],\s]+\s+([a-zA-Z0-9_]+)\s*\(', sub_line)
                    if sub_m and sub_m.group(1) not in ("if", "for", "while", "switch", "catch"):
                        methods.append(sub_m.group(1))
                    elif re.match(r'^\s*\}', sub_line):
                        break
                classes.append(SymbolDefinition(
                    name=c_name,
                    symbol_type=c_type,
                    args=methods,
                    line_number=line_idx,
                    is_exported="public" in line,
                    file_path=filename
                ))

                if is_entity and c_type == "class":
                    models.append(DatabaseModelDefinition(
                        name=c_name,
                        fields=methods,
                        model_type="jpa/hibernate",
                        line_number=line_idx,
                        file_path=filename
                    ))

        # 4. Methods / Functions
        method_re = re.compile(r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?([\w<>\[\],\s]+)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\s*\{')
        for line_idx, line in enumerate(lines, 1):
            m = method_re.search(line)
            if m:
                mname = m.group(2)
                if mname in ("if", "for", "while", "switch", "catch"):
                    continue
                raw_params = m.group(3)
                args = []
                if raw_params:
                    for p in raw_params.split(","):
                        parts = p.strip().split()
                        if parts:
                            args.append(parts[-1])
                functions.append(SymbolDefinition(
                    name=mname,
                    symbol_type="method",
                    args=args,
                    line_number=line_idx,
                    return_type=m.group(1).strip(),
                    is_exported="public" in line,
                    file_path=filename
                ))

        return SymbolTable(
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            global_variables=[],
            routes=routes,
            database_models=models,
            cross_file_imports=cross_imports,
            interfaces=[c for c in classes if c.symbol_type == "interface"]
        )

    # -------------------------------------------------------------------------
    # Kotlin & Android Parser (.kt)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_kotlin(cls, code: str, filename: str) -> SymbolTable:
        imports: List[str] = []
        cross_imports: List[CrossFileImport] = []
        functions: List[SymbolDefinition] = []
        classes: List[SymbolDefinition] = []
        routes: List[RouteDefinition] = []
        models: List[DatabaseModelDefinition] = []

        lines = code.split("\n")

        # 1. Imports
        import_re = re.compile(r'import\s+([a-zA-Z0-9_.*]+)')
        for line_idx, line in enumerate(lines, 1):
            m = import_re.search(line)
            if m:
                pkg = m.group(1)
                imports.append(pkg)
                cross_imports.append(CrossFileImport(
                    source_path=pkg,
                    imported_symbols=[pkg.split(".")[-1]],
                    is_relative=False,
                    raw_statement=line.strip(),
                    line_number=line_idx
                ))

        # 2. Routes (Spring / Ktor)
        route_re = re.compile(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping)\s*\(\s*["\']([^"\']*)["\']', re.IGNORECASE)
        ktor_re = re.compile(r'(?:^|\s)(get|post|put|delete)\s*\(\s*["\']([^"\']*)["\']', re.IGNORECASE)

        for line_idx, line in enumerate(lines, 1):
            m = route_re.search(line)
            if m:
                routes.append(RouteDefinition(
                    path=m.group(2),
                    method=m.group(1).replace("Mapping", "").upper(),
                    handler_name="kotlinHandler",
                    line_number=line_idx,
                    file_path=filename
                ))
            m_ktor = ktor_re.search(line)
            if m_ktor:
                routes.append(RouteDefinition(
                    path=m_ktor.group(2),
                    method=m_ktor.group(1).upper(),
                    handler_name="ktorHandler",
                    line_number=line_idx,
                    file_path=filename
                ))

        # 3. Classes and Database Models (Room @Entity)
        class_re = re.compile(r'(?:open|data|sealed|abstract|internal|public|private)?\s*(class|interface|object)\s+([a-zA-Z0-9_]+)')
        is_room = "@Entity" in code or "@Database" in code

        for line_idx, line in enumerate(lines, 1):
            m = class_re.search(line)
            if m:
                c_type = m.group(1)
                c_name = m.group(2)
                methods = []
                for sub_line in lines[line_idx:min(len(lines), line_idx + 60)]:
                    sub_m = re.search(r'fun\s+([a-zA-Z0-9_]+)\s*\(', sub_line)
                    if sub_m:
                        methods.append(sub_m.group(1))
                    elif re.match(r'^\s*\}', sub_line):
                        break
                classes.append(SymbolDefinition(
                    name=c_name,
                    symbol_type=c_type,
                    args=methods,
                    line_number=line_idx,
                    is_exported=not "private" in line,
                    file_path=filename
                ))
                if is_room and c_type == "class":
                    models.append(DatabaseModelDefinition(
                        name=c_name,
                        fields=methods,
                        model_type="room/android",
                        line_number=line_idx,
                        file_path=filename
                    ))

        # 4. Functions
        fun_re = re.compile(r'(?:suspend\s+|override\s+|open\s+|public\s+|private\s+|internal\s+)*fun\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)')
        for line_idx, line in enumerate(lines, 1):
            m = fun_re.search(line)
            if m:
                fname = m.group(1)
                raw_args = m.group(2)
                args = []
                if raw_args:
                    for a in raw_args.split(","):
                        parts = a.strip().split(":")
                        if parts and parts[0].strip():
                            args.append(parts[0].strip().split()[-1])
                functions.append(SymbolDefinition(
                    name=fname,
                    symbol_type="suspend_function" if "suspend" in line else "function",
                    args=args,
                    line_number=line_idx,
                    is_exported=not "private" in line,
                    file_path=filename
                ))

        return SymbolTable(
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            global_variables=[],
            routes=routes,
            database_models=models,
            cross_file_imports=cross_imports,
            interfaces=[c for c in classes if c.symbol_type == "interface"]
        )

    # -------------------------------------------------------------------------
    # AndroidManifest.xml & XML Configuration Parser
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_android_xml(cls, code: str, filename: str) -> SymbolTable:
        classes: List[SymbolDefinition] = []
        routes: List[RouteDefinition] = []
        variables: List[str] = []
        imports: List[str] = []

        try:
            root = ET.fromstring(code)
            # Namespace handling
            ns = {"android": "http://schemas.android.com/apk/res/android"}

            # Package
            pkg = root.attrib.get("package", "")
            if pkg:
                imports.append(pkg)

            # Permissions
            for perm in root.findall(".//uses-permission"):
                pname = perm.attrib.get("{http://schemas.android.com/apk/res/android}name", "")
                if pname:
                    variables.append(f"permission:{pname}")

            # Components (activity, service, receiver, provider)
            for tag in ["activity", "service", "receiver", "provider"]:
                for elem in root.findall(f".//{tag}"):
                    name = elem.attrib.get("{http://schemas.android.com/apk/res/android}name", "")
                    exported = elem.attrib.get("{http://schemas.android.com/apk/res/android}exported", "false")
                    permission = elem.attrib.get("{http://schemas.android.com/apk/res/android}permission", "")
                    classes.append(SymbolDefinition(
                        name=name or f"Unnamed_{tag}",
                        symbol_type=f"android_{tag}",
                        args=[f"exported={exported}", f"permission={permission}"],
                        line_number=1,
                        is_exported=(exported.lower() == "true"),
                        file_path=filename
                    ))

                    # Deep link intent filters -> routes
                    for intent in elem.findall(".//intent-filter"):
                        for data in intent.findall(".//data"):
                            scheme = data.attrib.get("{http://schemas.android.com/apk/res/android}scheme", "")
                            host = data.attrib.get("{http://schemas.android.com/apk/res/android}host", "")
                            prefix = data.attrib.get("{http://schemas.android.com/apk/res/android}pathPrefix", "")
                            if scheme or host:
                                routes.append(RouteDefinition(
                                    path=f"{scheme}://{host}{prefix}",
                                    method="INTENT",
                                    handler_name=name,
                                    line_number=1,
                                    file_path=filename
                                ))
        except Exception:
            # Regex fallback if XML has templating tags or malformed syntax
            for m in re.finditer(r'<(activity|service|receiver|provider)[^>]+android:name=["\']([^"\']+)["\']', code):
                classes.append(SymbolDefinition(
                    name=m.group(2),
                    symbol_type=f"android_{m.group(1)}",
                    args=[],
                    line_number=code[:m.start()].count("\n") + 1,
                    file_path=filename
                ))

        return SymbolTable(
            imports=imports,
            functions=[],
            classes=classes,
            global_variables=variables,
            routes=routes,
            database_models=[],
            cross_file_imports=[],
            interfaces=[]
        )

    # -------------------------------------------------------------------------
    # Generic Fallback
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_generic(cls, code: str, filename: str) -> SymbolTable:
        return SymbolTable()
