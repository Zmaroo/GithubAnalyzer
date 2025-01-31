# Sample Julia code with various function types

# Basic function definition
function greet(name::String)
    println("Hello, $name!")
end

# Short form function definition
square(x::Number) = x * x

# Function with multiple methods
function process(x::Int64)
    return x + 1
end

function process(x::String)
    return uppercase(x)
end

# Function with optional arguments
function calculate(a, b=10)
    return a * b
end

# Function with keyword arguments
function create_person(; name::String="John", age::Int=30)
    return (name=name, age=age)
end

# Anonymous function
multiply = (x, y) -> x * y

# Function with type parameters
function safe_get(dict::Dict{K,V}, key::K, default::V) where {K,V}
    return get(dict, key, default)
end

# Mutating function (convention: ends with !)
function push_unique!(arr::Vector{T}, item::T) where T
    if !(item in arr)
        push!(arr, item)
    end
    return arr
end

# Abstract type and function for multiple dispatch
abstract type Shape end

struct Circle <: Shape
    radius::Float64
end

struct Rectangle <: Shape
    width::Float64
    height::Float64
end

function area(shape::Circle)
    return π * shape.radius^2
end

function area(shape::Rectangle)
    return shape.width * shape.height
end

# Main execution
function main()
    # Test basic function
    greet("Alice")
    
    # Test short form function
    println(square(5))
    
    # Test multiple dispatch
    println(process(42))
    println(process("hello"))
    
    # Test optional arguments
    println(calculate(5))
    println(calculate(5, 20))
    
    # Test keyword arguments
    person = create_person(name="Bob", age=25)
    println(person)
    
    # Test anonymous function
    println(multiply(6, 7))
    
    # Test generic function
    dict = Dict("a" => 1, "b" => 2)
    println(safe_get(dict, "c", 0))
    
    # Test mutating function
    numbers = [1, 2, 3]
    push_unique!(numbers, 2)
    push_unique!(numbers, 4)
    println(numbers)
    
    # Test shape hierarchy
    circle = Circle(5.0)
    rectangle = Rectangle(4.0, 6.0)
    println(area(circle))
    println(area(rectangle))
end

# Call main function
main() 