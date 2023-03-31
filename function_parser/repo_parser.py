import logging
import ast
import builtins

from ast import Attribute, ClassDef, IfExp, Import, ImportFrom, Name, Subscript, expr
from ast import Call as AstCall

from models.call import Call
from models.file import File
from models.folder import Folder
from models.repository import Repository

logger = logging.getLogger(__name__)

class RepoParser:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository
        self.folder_names = {item.name for item in repository.directory.walk(Folder)}
        self.builtins = {name for name, call in vars(builtins).items() if getattr(call, '__call__', None)}
        self.file_names = {
            item.name for item in repository.directory.walk(File) if item.data
        }

    def _get_call_path(self, item: expr) -> list[str]:
        """Get a list of names from method call"""
        path = []
        # TODO searching args too?
        while True:
            type_ = type(item)
            if type_ is Name:
                path.append(item.id)
                break
            elif type_ is Attribute:
                path.append(item.attr)
                item = item.value
            elif type_ is AstCall:
                item = item.func
            elif type_ is Subscript:
                item = item.value
            elif type_ is IfExp:
                # TODO skipping ifs atm
                break
            else:
                break
        return path[::-1]

    def _get_import_path(
        self,
        call: AstCall,
        call_path: list[str],
        classes: list[ClassDef],
        file_imports: list[ImportFrom | Import],
    ) -> list[str]:
        """Get the full function path from the module"""
        first_call = call_path[0]
        if first_call == "super":
            # We search for the inherited class
            for class_ in classes:
                called_in_class = call.lineno in range(
                    class_.lineno, class_.end_lineno + 1
                )
                if called_in_class and class_.bases:
                    # TODO MULTIPLE INHERITANCES
                    class_path = self._get_call_path(class_.bases[0])
                    call_path = class_path + call_path
                    first_call = call_path[0]
                    break
                elif called_in_class and not class_.bases:
                    return []
        for import_ in file_imports:
            if first_call in (alias.name for alias in import_.names):
                if isinstance(import_, ImportFrom):
                    call_path = import_.module.split(".") + call_path
                return call_path
        if first_call in self.builtins:
            return call_path

    def _is_local(self, path: list[str]) -> bool:
        """
        Considers local import if the first two package/modules matches the local folders
        """
        package = path[0]
        return package in self.folder_names or package in self.file_names

    def get_call_full_path(self, call: Call) -> list[str] | None:
        function_path = self._get_call_path(call)
        full_path = None
        if function_path:
            full_path = self._get_import_path(
                call, function_path, self.file_classes, self.file_imports
            )
        return full_path

    def get_file_calls(self, file: File) -> list[Call]:
        """
        Get all the full path of every external method call, uses the folder and
        file names to filter local imports
        """
        calls = []
        if not file.data:
            return calls
        try:
            module = ast.parse(file.data)
        except SyntaxError:
            return calls

        def is_import(x):
            return (
                isinstance(x, (Import)) or isinstance(x, (ImportFrom)) and x.level == 0
            )

        self.file_imports = [node for node in ast.walk(module) if is_import(node)]
        self.file_classes = [node for node in ast.walk(module) if isinstance(node, ClassDef)]
        function_calls = (
            node for node in ast.walk(module) if isinstance(node, AstCall)
        )
        for call in function_calls:
            full_path = self.get_call_full_path(call)
            if full_path and not self._is_local(full_path):
                calls.append(Call(".".join(full_path), call.lineno, file))
        return calls

    def get_repo_calls(self) -> set[Call]:
        logger.info(f"Parsing {len(self.file_names)} files from {self.repository.name}")
        all_calls = set()
        for file in self.repository.directory.walk(File):
            logger.debug(f"Reading {file.name}  --> {file.web_url}")
            file_calls = self.get_file_calls(file)
            all_calls.update(call for call in file_calls if call not in all_calls)
        return all_calls
