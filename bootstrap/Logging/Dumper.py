from Parser.AST import ASTNode


def ast_to_json(node):
    if isinstance(node, ASTNode):
        result = {"node_type": node.node_type}

        for field, value in node.__dict__.items():
            result[field] = ast_to_json(value)

        return result

    elif isinstance(node, list):
        return [ast_to_json(x) for x in node]

    elif isinstance(node, dict):
        return {k: ast_to_json(v) for k, v in node.items()}

    elif isinstance(node, (str, int, float, bool)) or node is None:
        return node

    # Type system, enums, etc
    elif hasattr(node, "name"):
        return node.name

    # fallback
    return str(node)
