#include <iostream>
#include <vector>
#include <functional>

// Regular function
int add(int a, int b) {
    return a + b;
}

// Function template
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

// Lambda function
auto multiply = [](int x, int y) { return x * y; };

// Class with member functions
class Calculator {
public:
    // Constructor
    Calculator() : value(0) {}

    // Member function
    void add(int x) {
        value += x;
    }

    // Const member function
    int getValue() const {
        return value;
    }

    // Static member function
    static int multiply(int x, int y) {
        return x * y;
    }

    // Virtual function
    virtual void display() {
        std::cout << "Value: " << value << std::endl;
    }

private:
    int value;
};

// Derived class with override
class AdvancedCalculator : public Calculator {
public:
    // Override virtual function
    void display() override {
        std::cout << "Advanced Calculator Value: " << getValue() << std::endl;
    }
};

// Function with reference parameter
void increment(int& x) {
    x++;
}

// Function with default arguments
void print(std::string message = "Hello") {
    std::cout << message << std::endl;
}

// Function returning lambda
auto get_multiplier(int factor) {
    return [factor](int x) { return x * factor; };
}

// Namespace with functions
namespace Math {
    double square(double x) {
        return x * x;
    }

    namespace Advanced {
        double cube(double x) {
            return x * x * x;
        }
    }
}

// Main function
int main() {
    Calculator calc;
    calc.add(5);
    return 0;
} 