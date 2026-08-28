from typing import Any, List, Optional
import os
from Parser.AST import (
    AssignmentStatement,
    ReassignmentStatement,
    MemberReassignmentStatement,
    IndexReassignmentStatement,
    BlockStatement,
    FunctionStatement,
    StructureStatement,
    ClassStatement,
    EnumeratorStatement,
    ScopeStatement,
    ReturnStatement,
    WhenStatement,
    DoStatement,
    ImportStatement,
    FromImportStatement,
    ObjectStatement,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    ExportStatement,
    WithStatement,
    NothingLiteral,
    IteratorLiteral,
    TaskStatement,
)
from Interpreter.Runtime import (
    Environment,
    FunctionObject,
    StructureObject,
    ClassObject,
    InstanceObject,
    ModuleObject,
    EnumeratorObject,
    VariantObject,
    BaseObject,
    TaskObject,
)
from Interpreter.Exceptions import ReturnException, RaiseException, RuntimeBreak, RuntimeContinue
from Lexer.Lexer import Lexer
from Parser.Parser import Parser

class StatementHandler:
    def _evaluate_assignment_statement(
        self, node: AssignmentStatement, environment: Environment
    ) -> any:
        value: any = None

        try:
            value = self._evaluate(node.value, environment)
        except ReturnException as return_exception:
            value = return_exception.value

        type: str = getattr(node, "resolved_type", None) or getattr(
            node, "declared_type", None
        )

        is_set = getattr(node, "is_set", False) or getattr(node, "name_keyword", "") == "set"

        if is_set and environment.has(node.name):
            environment.assign(node.name, value)
            return value

        if not environment.has(node.name) and environment.has("self"):
             self_object = environment.get("self")
             if isinstance(self_object, BaseObject):
                  try:
                       self_object.set_member(node.name, value)
                       return value
                  except Exception:
                       pass

        environment.define(node.name, value, mutable=node.mutable, type=type)
        return value

    def _evaluate_dereference_reassignment_statement(
        self, node: Any, environment: Environment
    ) -> any:
        ptr = self._evaluate(node.pointer_expression, environment)
        value = self._evaluate(node.value, environment)
        
        from Interpreter.Runtime import PointerObject
        if isinstance(ptr, PointerObject):
            ptr.set_value(value)
            return value
        raise RuntimeError(f"Cannot dereference assign to non-pointer object of type {type(ptr)}")

    def _evaluate_reassignment_statement(
        self, node: ReassignmentStatement, environment: Environment
    ) -> any:
        value: any = self._evaluate(node.value, environment)

        if environment.has(node.name):
             environment.assign(node.name, value)
             return value

        if environment.has("self"):
             self_object = environment.get("self")
             if isinstance(self_object, BaseObject):
                  try:
                       self_object.set_member(node.name, value)
                       return value
                  except Exception:
                       pass

        raise RuntimeError(f"Undefined variable '{node.name}'")

    def _evaluate_member_reassignment_statement(
        self, node: MemberReassignmentStatement, environment: Environment
    ):
        object: BaseObject = self._evaluate(node.callee, environment)
        value: any = self._evaluate(node.value, environment)
        member_name: str = node.property
        if hasattr(member_name, "name"):
            member_name = member_name.name

        if isinstance(object, (StructureObject, InstanceObject)):
            object.set_member(member_name, value)
            return value

        # Map / built-in module context (e.g. module.entry -> `run`)
        if isinstance(object, dict):
            object[member_name] = value
            return value

        raise RuntimeError(
            f"Cannot assign to member '{member_name}' of non-structure/non-instance object"
        )

    def _evaluate_index_reassignment_statement(
        self, node: IndexReassignmentStatement, environment: Environment
    ):
        object_val: BaseObject | list | dict = self._evaluate(node.callee, environment)
        index_val: any = self._evaluate(node.index, environment)
        value: any = self._evaluate(node.value, environment)

        if isinstance(object_val, (list, bytearray)):
            if not isinstance(index_val, int):
                raise RuntimeError(f"Index must be an integer for {type(object_val).__name__}, got {type(index_val).__name__}")
            if index_val < 0 or index_val >= len(object_val):
                 raise RuntimeError(f"Index out of bounds: {index_val}")
            
            if isinstance(object_val, bytearray):
                if not isinstance(value, int) or value < 0 or value > 255:
                     raise RuntimeError(f"Byte value must be an integer between 0 and 255, got {value}")

            object_val[index_val] = value
            return value
        
        if isinstance(object_val, dict):
             object_val[index_val] = value
             return value

        raise RuntimeError(f"Cannot assign by index to object of type {type(object_val)}")

    def _evaluate_block_statement(
        self, node: BlockStatement, environment: Environment
    ) -> any:
        new_environment = Environment(parent=environment)
        new_environment.defers = []

        result: any = None

        try:
            for statement in node.statements:
                try:
                    result = self._evaluate(statement, new_environment)

                except ReturnException:
                    raise

                except RuntimeBreak:
                    raise

                except RuntimeContinue:
                    raise

                except RaiseException:
                    raise
            
            return result
        finally:
            if hasattr(new_environment, "defers"):
                for defer_node in reversed(new_environment.defers):
                    self._evaluate(defer_node.body, environment)

    def _evaluate_function_statement(
        self, node: FunctionStatement, environment: Environment
    ) -> FunctionObject:
        function_object: FunctionObject = FunctionObject(
            name=node.name,
            parameters=node.parameters,
            body=node.body,
            closure=environment,
            return_type=getattr(node, "resolved_type", None)
            or getattr(node, "inferred_return_type", None),
        )

        environment.define(node.name, function_object, mutable=False, type="Function")

        return function_object

    def _evaluate_task_statement(self, node: TaskStatement, environment: Environment) -> Any:
        task_object = TaskObject(
            node.name,
            node.parameters,
            node.body,
            environment,
            getattr(node, "return_type", None)
        )
        environment.define(node.name, task_object, mutable=False, type="Task")
        return task_object

    def _evaluate_structure_statement(
        self, node: StructureStatement, environment: Environment
    ) -> any:
        members: dict = {}

        for member in node.members:
            value: any = (
                self._evaluate(member.value, environment)
                if member.value
                else NothingLiteral()
            )
            members[member.name] = {
                "type": member.declared_type,
                "value": value,
                "mutable": member.mutable,
            }

        parent_obj = None
        if hasattr(node, "parent") and node.parent:
            parent_obj = environment.get(node.parent)

        structure_object: StructureObject = StructureObject(
            name=node.name,
            members=members,
            closure=environment,
            parent=parent_obj,
            reflectable=bool(getattr(node, "reflectable", False)),
        )

        environment.define(node.name, structure_object, False, "structure")
        # Type metadata registry for zen.reflect
        if hasattr(self, "_reflect_register_type"):
            self._reflect_register_type(
                node.name,
                list(members.keys()),
                [],
                bool(getattr(node, "reflectable", False)),
            )

        return structure_object

    def _evaluate_class_statement(self, node: ClassStatement, environment: Environment) -> ClassObject:
        parent: ClassObject | None = None
        if node.parent:
            parent = environment.get(node.parent)
            if not isinstance(parent, ClassObject):
                 raise RuntimeError(f"Parent '{node.parent}' is not a class")

        class_object = ClassObject(
            name=node.name,
            parent=parent,
            members=node.members,
            methods=node.methods,
            closure=environment,
            reflectable=bool(getattr(node, "reflectable", False)),
        )

        for method_ast in node.methods:
             function_object = FunctionObject(
                name=method_ast.name,
                parameters=method_ast.parameters,
                body=method_ast.body,
                closure=environment,
                return_type=getattr(method_ast, "resolved_type", None)
             )
             class_object.methods_map[method_ast.name] = function_object

        environment.define(node.name, class_object, False, "class")
        if hasattr(self, "_reflect_register_type"):
            self._reflect_register_type(
                node.name,
                class_object.field_names(),
                class_object.method_names(),
                bool(getattr(node, "reflectable", False)),
            )
        return class_object

    def _evaluate_enumerator_statement(
        self, node: EnumeratorStatement, environment: Environment
    ) -> any:
        members: dict = {}

        for variant in node.members:
            variant_name = variant.name
            params = variant.params
            
            if not params:
                members[variant_name] = {
                    "type": "Variant",
                    "value": VariantObject(node.name, variant_name, []),
                    "mutable": False,
                }
            else:
                def make_constructor(e_name, v_name, v_params):
                    def constructor(*args_eval):
                        if len(args_eval) != len(v_params):
                            raise Exception(
                                f"Variant {v_name} expects {len(v_params)} arguments, got {len(args_eval)}"
                            )
                        return VariantObject(e_name, v_name, list(args_eval))

                    return constructor
                
                members[variant_name] = {
                    "type": "Function",
                    "value": make_constructor(node.name, variant_name, params),
                    "mutable": False,
                }

        structure_object: EnumeratorObject = EnumeratorObject(
            name=node.name, members=members, closure=environment
        )

        environment.define(node.name, structure_object, False, "Enumerator")

        return structure_object

    def _evaluate_scope_statement(self, node: ScopeStatement, environment: Environment) -> any:
        scope_env = Environment(parent=environment, file_path=environment.file_path)

        if hasattr(node.body, "statements"):
             for statement in node.body.statements:
                 self._evaluate(statement, scope_env)

        scope_object = ModuleObject(node.name, scope_env)

        environment.define(node.name, scope_object, False, "scope")
        return scope_object

    def _evaluate_return_statement(
        self, node: ReturnStatement, environment: Environment
    ) -> any:
        value: any = (
            self._evaluate(node.value, environment) if node.value is not None else None
        )
        raise ReturnException(value)

    def _evaluate_when_statement(
        self, node: WhenStatement, environment: Environment
    ) -> any:
        condition_val = self._evaluate(node.condition, environment)
        
        if hasattr(node, "branches") and node.branches is not None:
            for branch in node.branches:
                branch_env = Environment(parent=environment)
                if self._evaluate_pattern_match(condition_val, branch.pattern, branch_env):
                    if branch.guard:
                        if not self._evaluate(branch.guard, branch_env):
                            continue
                    return self._evaluate(branch.body, branch_env)
            
            if node.or_block:
                return self._evaluate(node.or_block, environment)
            return None

        if condition_val:
            if node.when_block:
                return self._evaluate(node.when_block, environment)
            return None

        for condition_statement in node.conditional_blocks or []:
            if self._evaluate(condition_statement["condition"], environment):
                if condition_statement.get("block"):
                    return self._evaluate(condition_statement["block"], environment)
                return None

        if node.or_block:
            return self._evaluate(node.or_block, environment)

        return None

    def _evaluate_do_statement(
        self, node: DoStatement, environment: Environment
    ) -> any:
        do_type: str = node.do_type
        result: any = None
        loop_cycled: bool = False

        new_environment = Environment(parent=environment)

        try:
            if do_type == "while":
                while self._evaluate(node.condition, new_environment):
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

            elif do_type == "until":
                while not self._evaluate(node.condition, new_environment):
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

            elif do_type == "while_post":
                while True:
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        pass
                    except RuntimeBreak:
                        break
                    if not self._evaluate(node.condition, new_environment):
                        break

            elif do_type == "until_post":
                while True:
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        pass
                    except RuntimeBreak:
                        break
                    if self._evaluate(node.condition, new_environment):
                        break

            elif do_type == "for":
                iterable_value: any = self._evaluate(node.iterable, new_environment)
                if not hasattr(iterable_value, "__iter__"):
                    raise RuntimeError(f"Object '{iterable_value}' is not iterable")

                for item in iterable_value:
                    loop_cycled = True
                    loop_environment: Environment = Environment(new_environment)
                    try:
                        if isinstance(node.iterator, list):
                            if isinstance(item, (list, tuple)):
                                for i, variable in enumerate(node.iterator):
                                    loop_environment.define(
                                        variable.name, item[i], True
                                    )
                            else:
                                raise RuntimeError("Cannot destructure non-tuple value in for loop")
                        elif isinstance(node.iterator, IteratorLiteral):
                            if isinstance(item, (list, tuple)):
                                for i, variable in enumerate(node.iterator.value):
                                    name: str = None
                                    if hasattr(variable, "name"):
                                        name = variable.name
                                    elif hasattr(variable, "value"):
                                        name = variable.value
                                    loop_environment.define(name, item[i], True, getattr(variable, 'type', None))
                            else:
                                raise RuntimeError("Cannot destructure non-tuple value in for loop")
                        else:
                            name: str = node.iterator
                            if hasattr(node.iterator, "name"):
                                name = node.iterator.name
                            elif hasattr(node.iterator, "value"):
                                name = node.iterator.value
                            loop_environment.define(name, item, mutable=True)
                        result = self._evaluate(node.body, loop_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break
                if not loop_cycled and node.or_block:
                    result = self._evaluate(node.or_block, new_environment)

            elif do_type == "block":
                while True:
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

        except ReturnException:
            raise

        if (do_type in ("while", "until", "while_post", "until_post")) and node.or_block and not loop_cycled:
            result = self._evaluate(node.or_block, new_environment)

        return result

    def _evaluate_import_statement(self, node: ImportStatement, environment: Environment) -> any:
        module_object = self._load_module(node.path, node.name, caller_path=environment.file_path)
        environment.define(node.name, module_object, False, "module")
        return module_object

    def _evaluate_from_import_statement(self, node: FromImportStatement, environment: Environment) -> any:
        module_object = self._load_module(node.path, node.path, caller_path=environment.file_path)
        for symbol_info in node.symbols:
            name = symbol_info["name"]
            alias = symbol_info.get("alias") or name
            try:
                value = module_object.get_member(name)
            except RuntimeError:
                 raise RuntimeError(f"Module '{node.path}' has no member '{name}'")
            environment.define(alias, value, False, "imported_symbol")
        return None

    def _evaluate_with_statement(self, node: WithStatement, environment: Environment) -> any:
        resource = self._evaluate(node.expression, environment)
        if hasattr(resource, "get_member"):
            try:
                push_fn = resource.get_member("push")
                if push_fn:
                    self._call_function(push_fn, [])
            except:
                pass
        new_env = Environment(parent=environment)
        if node.alias:
            new_env.define(node.alias, resource, False, "resource")
        try:
            result = self._evaluate(node.body, new_env)
            return result
        finally:
            if hasattr(resource, "get_member"):
                try:
                    pop_fn = resource.get_member("pop")
                    if pop_fn:
                        self._call_function(pop_fn, [])
                except:
                    pass

    def _evaluate_defer_statement(self, node: DeferStatement, environment: Environment):
        if not hasattr(environment, "defers"):
            environment.defers = []
        environment.defers.append(node)

    def _evaluate_raise_statement(self, node: RaiseStatement, environment: Environment):
        value = self._evaluate(node.value, environment)
        with_value = self._evaluate(node.with_value, environment) if node.with_value else None
        raise RaiseException(value, with_value)

    def _evaluate_assert_statement(self, node: AssertStatement, environment: Environment):
        condition = self._evaluate(node.condition, environment)
        if not condition:
            if node.raise_expression:
                 raise RaiseException(self._evaluate(node.raise_expression, environment))
            raise RaiseException(f"Assertion failed: {node.condition}")

    def _evaluate_check_statement(self, node: CheckStatement, environment: Environment):
        try:
            matched_value = self._evaluate(node.expression, environment)
            for case in node.cases:
                branch_env = Environment(parent=environment)
                if self._evaluate_pattern_match(matched_value, case.pattern, branch_env):
                    if case.guard:
                        if not self._evaluate(case.guard, branch_env):
                            continue
                    return self._evaluate(case.body, branch_env)
            return matched_value
        except RaiseException as e:
            for case in node.cases:
                branch_env = Environment(parent=environment)
                if self._evaluate_pattern_match(e, case.pattern, branch_env):
                    if case.guard:
                        if not self._evaluate(case.guard, branch_env):
                            continue
                    return self._evaluate(case.body, branch_env)
            
            if node.or_block:
                return self._evaluate(node.or_block, environment)
            if hasattr(node, "raise_expression") and node.raise_expression:
                raise_val = self._evaluate(node.raise_expression, environment)
                raise RaiseException(raise_val)
            raise e

    def _evaluate_object_statement(self, node: ObjectStatement, environment: Environment):
        members: dict = {}
        for member in node.members:
            value = self._evaluate(member.value, environment) if member.value else NothingLiteral()
            members[member.name] = {"type": member.declared_type, "value": value, "mutable": member.mutable}
        parent_obj = environment.get(node.parent) if node.parent else None
        obj = StructureObject(name=node.name, members=members, closure=environment, parent=parent_obj)
        environment.define(node.name, obj, False, "object")
        return obj

    def _evaluate_export_statement(self, node: ExportStatement, environment: Environment):
        return self._evaluate(node.statement, environment)
