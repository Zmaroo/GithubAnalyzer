QUERY_PATTERNS = {
    "groovy": {
        "function": """
            [
                (method_definition)
                (constructor_definition)
                (closure_expression)
            ] @function
        """
    },
    
    "racket": {
        "function": """
            [
                (definition)
                (lambda)
                (function)
            ] @function
        """
    },
    
    "clojure": {
        "function": """
            [
                (list_lit 
                    name: [
                        (symbol) @name
                        (#match? @name "^(defn|fn)$")
                    ]
                )
            ] @function
        """
    },
    
    "elixir": {
        "function": """
            [
                (call
                    target: [
                        (identifier) @name
                        (#match? @name "^(def|defp)$")
                    ]
                )
                (anonymous_function)
            ] @function
        """
    },
    
    "haxe": {
        "function": """
            [
                (function_declaration)
                (method_declaration)
                (constructor_declaration)
                (arrow_function)
                (abstract_function)
            ] @function
        """
    },
} 