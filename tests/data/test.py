"""Test file for tree-sitter parsing."""

def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

class Greeter:
    """A class that greets people."""
    
    def __init__(self, greeting: str = "Hello"):
        """Initialize with a custom greeting."""
        self.greeting = greeting
        
    def greet(self, name: str) -> str:
        """Greet someone."""
        return f"{self.greeting}, {name}!"
        
    @property
    def formal_greeting(self) -> str:
        """Get a more formal version of the greeting."""
        return f"{self.greeting} and good day"

def main():
    """Main function."""
    greeter = Greeter("Hi")
    print(greeter.greet("World"))
    print(greeter.formal_greeting)

if __name__ == "__main__":
    main() 