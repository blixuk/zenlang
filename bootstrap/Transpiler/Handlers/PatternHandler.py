from typing import Any
from Parser.AST import *
from Transpiler.MIR import *

class PatternHandler:
    def _pattern_bind_name(self, pattern: Any) -> str:
        """C name for a pattern binding — must match body identifier mangling."""
        from Parser.AST import Identifier
        raw = getattr(pattern, "name", None) or "pat"
        # Build a fake Identifier so we share get_mangled_name rules
        # (module prefix from filename, no nested _L when scope_level is 0).
        ident = Identifier(
            getattr(pattern, "line", 0) or 0,
            getattr(pattern, "column", 0) or 0,
            getattr(pattern, "scope_level", 1) or 1,
            raw,
            "Variable",
        )
        if hasattr(pattern, "filename") and pattern.filename:
            ident.filename = pattern.filename
        elif getattr(self, "filename", None):
            ident.filename = self.filename
        if hasattr(pattern, "symbol") and pattern.symbol is not None:
            ident.symbol = pattern.symbol
        return self.get_mangled_name(ident)

    def _visit_pattern_match(self, subject: str, pattern: Any, node: ASTNode) -> str:
        current_reg = self.current_region
        tmp_match = self._alloc_temp(self.new_label("tmp_match"), node, region=current_reg)
        
        if isinstance(pattern, WildcardPattern):
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            return tmp_match
            
        if isinstance(pattern, IdentifierPattern):
            # Bind by copy (Borrow), not Move — later cases still need the subject.
            mangled_name = self._pattern_bind_name(pattern)
            self._emit(Alloc(target=mangled_name, region="global", type=None), node)
            self._emit(Borrow(dest=mangled_name, src=subject), node)
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            return tmp_match

        if isinstance(pattern, RestPattern):
            # Rest of a list from the current index is handled by ListPattern;
            # standalone rest binds the whole subject.
            mangled_name = self._pattern_bind_name(pattern)
            self._emit(Alloc(target=mangled_name, region="global", type=None), node)
            self._emit(Borrow(dest=mangled_name, src=subject), node)
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            return tmp_match

        if isinstance(pattern, IsMatchPattern):
            self._emit(Call(target=tmp_match, callee="ZenValue_is_type_name", args=[subject, f'"{pattern.type_name}"'], region=current_reg), node)
            return tmp_match

        if isinstance(pattern, ListPattern):
            # 1. Check if subject is a list
            is_list = self._alloc_temp(self.new_label("is_list"), node, region=current_reg)
            self._emit(Call(target=is_list, callee="ZenValue_is_type_name", args=[subject, '"List"'], region=current_reg), node)
            self._emit(Move(dest=tmp_match, src=is_list), node)

            elements = list(pattern.elements or [])
            has_rest = bool(elements) and isinstance(elements[-1], RestPattern)
            fixed = elements[:-1] if has_rest else elements

            # Length constraint: exact when no rest, min length when rest present.
            len_tmp = self._alloc_temp(self.new_label("list_len"), node, region=current_reg)
            self._emit(Call(target=len_tmp, callee="ZenValue_get_length", args=[subject], region=current_reg), node)
            need_tmp = self._alloc_temp(self.new_label("need_len"), node, "int", region=current_reg)
            self._emit(Load(target=need_tmp, source=str(len(fixed)), type="int"), node)
            len_ok = self._alloc_temp(self.new_label("len_ok"), node, region=current_reg)
            if has_rest:
                self._emit(Compute(target=len_ok, op=">=", left=len_tmp, right=need_tmp), node)
            else:
                self._emit(Compute(target=len_ok, op="==", left=len_tmp, right=need_tmp), node)
            self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=len_ok), node)
            
            for i, elem_pattern in enumerate(fixed):
                elem_val = self._alloc_temp(self.new_label("elem_val"), node, region=current_reg)
                idx_tmp = self._alloc_temp(self.new_label("idx"), node, "int", region=current_reg)
                self._emit(Load(target=idx_tmp, source=str(i), type="int"), node)
                self._emit(Call(target=elem_val, callee="Value_get_index", args=[subject, idx_tmp], region=current_reg), node)
                elem_match = self._visit_pattern_match(elem_val, elem_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=elem_match), node)

            if has_rest:
                rest_pat = elements[-1]
                rest_val = self._alloc_temp(self.new_label("rest_val"), node, region=current_reg)
                start_tmp = self._alloc_temp(self.new_label("rest_start"), node, "int", region=current_reg)
                self._emit(Load(target=start_tmp, source=str(len(fixed)), type="int"), node)
                self._emit(Call(target=rest_val, callee="ZenList_slice_from", args=[subject, start_tmp], region=current_reg), node)
                rest_match = self._visit_pattern_match(rest_val, rest_pat, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=rest_match), node)

            return tmp_match

        if isinstance(pattern, MapPattern):
            # 1. Check if subject is a Map
            is_map = self._alloc_temp(self.new_label("is_map"), node, region=current_reg)
            self._emit(Call(target=is_map, callee="ZenValue_is_type_name", args=[subject, '"Map"'], region=current_reg), node)
            self._emit(Move(dest=tmp_match, src=is_map), node)
            
            for key_node, val_pattern in pattern.pairs:
                key_val = self._visit_expression(key_node)
                val_val = self._alloc_temp(self.new_label("val_val"), node, region=current_reg)
                self._emit(Call(target=val_val, callee="Value_get_index", args=[subject, key_val], region=current_reg), node)
                val_match = self._visit_pattern_match(val_val, val_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=val_match), node)
            return tmp_match

        if isinstance(pattern, LiteralPattern):
            val = self._visit_expression(pattern.value)
            self._emit(Compute(target=tmp_match, op="==", left=subject, right=val), node)
            return tmp_match

        if isinstance(pattern, DestructurePattern):
            # Structure field match: Point { x, y } or Point { x -> x_val }
            # Treat as always-true type shape for bootstrap; bind fields.
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            for field_name, member_pattern in (pattern.members or []):
                field = field_name
                if hasattr(field, "name"):
                    field = field.name
                if hasattr(field, "value"):
                    field = field.value
                field = str(field)
                field_val = self._alloc_temp(self.new_label("field_val"), node, region=current_reg)
                self._emit(GetAttr(target=field_val, obj=subject, prop=field, type=None), node)
                member_match = self._visit_pattern_match(field_val, member_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=member_match), node)
            return tmp_match

        if isinstance(pattern, VariantPattern):
            if not pattern.enum_name and not pattern.params:
                type_check = self._alloc_temp(self.new_label("type_check"), node, "bool", region=current_reg)
                self._emit(Call(target=type_check, callee="ZenValue_is_type_name", args=[subject, f'"{pattern.name}"'], region=current_reg), node)
                var_check = self._alloc_temp(self.new_label("var_check"), node, "bool", region=current_reg)
                zen_enum = self._alloc_temp(self.new_label("zen_enum"), node, "string", region=current_reg)
                self._emit(Load(target=zen_enum, source='""', type="string"), node)
                zen_variant = self._alloc_temp(self.new_label("zen_variant"), node, "string", region=current_reg)
                self._emit(Load(target=zen_variant, source=f'"{pattern.name}"', type="string"), node)
                self._emit(Call(target=var_check, callee="ZenValue_is_variant", args=[subject, zen_enum, zen_variant], region=current_reg), node)
                self._emit(Compute(target=tmp_match, op="or", left=type_check, right=var_check), node)
                return tmp_match

            # Use the 3-argument ZenValue_is_variant(val, enum, variant)
            zen_enum = self._alloc_temp(self.new_label("zen_enum"), node, "string", region=current_reg)
            self._emit(Load(target=zen_enum, source=f"`{pattern.enum_name}`", type="string"), node)
            
            zen_variant = self._alloc_temp(self.new_label("zen_variant"), node, "string", region=current_reg)
            self._emit(Load(target=zen_variant, source=f"`{pattern.name}`", type="string"), node)
            
            self._emit(Call(target=tmp_match, callee="ZenValue_is_variant", args=[subject, zen_enum, zen_variant], region=current_reg), node)
            
            # 3. Destructure params
            for i, param_pattern in enumerate(pattern.params):
                param_val = self._alloc_temp(self.new_label("param_val"), node, region=current_reg)
                idx_tmp = self._alloc_temp(self.new_label("idx"), node, "int", region=current_reg)
                self._emit(Load(target=idx_tmp, source=str(i), type="int"), node)
                self._emit(Call(target=param_val, callee="ZenValue_get_variant_data", args=[subject, idx_tmp], region=current_reg), node)
                
                param_match = self._visit_pattern_match(param_val, param_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=param_match), node)
            
            return tmp_match
        
        # Unknown pattern: fail closed
        self._emit(Load(target=tmp_match, source="false", type="bool"), node)
        return tmp_match
