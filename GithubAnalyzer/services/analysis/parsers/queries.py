QUERIES = {
    "groovy": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
                (closure_expression)
            ] @function
        """
    },
    "zig": {
        "function": """
            [
                (FnProto)
                (fn)
                (pub)
            ] @function
        """
    },
    "commonlisp": {
        "function": """
            [
                (defun)
                (defun_header)
                (defun_keyword)
                (defmethod)
            ] @function
        """
    },
    "elixir": {
        "function": """
            [
                (fn)
                (def)
                (defp)
            ] @function
        """
    },
    "erlang": {
        "function": """
            [
                (fun_decl)
                (fun)
                (fun_clause)
                (function_clause)
            ] @function
        """
    },
    "purescript": {
        "function": """
            [
                (function)
                (exp_lambda)
                (value_declaration)
            ] @function
        """
    },
    "dart": {
        "function": """
            [
                (function_signature)
                (method_signature)
                (constructor_signature)
                (function_expression)
                (function_body)
            ] @function
        """
    },
    "gleam": {
        "function": """
            [
                (fn)
                (pub_fn)
            ] @function
        """
    },
    "hack": {
        "function": """
            [
                (function)
                (function_declaration)
                (method_declaration)
            ] @function
        """
    },
    "haxe": {
        "function": """
            [
                (function)
                (function_declaration)
                (function_arg)
            ] @function
        """
    },
    "java": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "javascript": {
        "function": """
            [
                (function_declaration)
                (method_definition)
                (arrow_function)
            ] @function
        """
    },
    "python": {
        "function": """
            [
                (function_definition)
                (lambda)
            ] @function
        """
    },
    "ruby": {
        "function": """
            [
                (method)
                (singleton_method)
            ] @function
        """
    },
    "scala": {
        "function": """
            [
                (function_definition)
                (class_definition)
            ] @function
        """
    },
    "typescript": {
        "function": """
            [
                (function_declaration)
                (method_definition)
                (arrow_function)
            ] @function
        """
    },
    "c": {
        "function": """
            [
                (function_definition)
            ] @function
        """
    },
    "c++": {
        "function": """
            [
                (function_definition)
                (method_definition)
            ] @function
        """
    },
    "go": {
        "function": """
            [
                (function_declaration)
                (method_declaration)
            ] @function
        """
    },
    "kotlin": {
        "function": """
            [
                (function_declaration)
                (class_declaration)
            ] @function
        """
    },
    "rust": {
        "function": """
            [
                (function_item)
                (closure_expression)
            ] @function
        """
    },
    "swift": {
        "function": """
            [
                (function_declaration)
                (initializer_declaration)
                (deinitializer_declaration)
                (closure_expression)
            ] @function
        """
    },
    "php": {
        "function": """
            [
                (function_definition)
                (method_declaration)
            ] @function
        """
    },
    "matlab": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "octave": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "r": {
        "function": """
            [
                (function_definition)
            ] @function
        """
    },
    "shell": {
        "function": """
            [
                (function_definition)
            ] @function
        """
    },
    "sql": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "xml": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "yaml": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "html": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    },
    "css": {
        "function": """
            [
                (method_declaration)
                (constructor_declaration)
            ] @function
        """
    }
} 