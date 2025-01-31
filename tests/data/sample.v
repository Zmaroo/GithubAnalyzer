module main

// Type definitions
struct User {
mut:
    name string
    age  int
}

// Interface definition
interface Processable {
mut:
    process() !string
}

// Implement interface for User
fn (u User) process() !string {
    if u.age < 0 {
        return error('Invalid age')
    }
    if u.age < 18 {
        return error('Underage')
    }
    return 'Adult user'
}

// Constructor function
fn new_user(name string, age int) !User {
    if age < 0 {
        return error('Age cannot be negative')
    }
    return User{
        name: name
        age: age
    }
}

// Method with return value
fn (u User) is_adult() bool {
    return u.age >= 18
}

// Method with string formatting
fn (u User) str() string {
    return '$u.name ($u.age years old)'
}

// Function with optional parameter
fn create_greeting(name string, prefix ?string) string {
    p := prefix or { 'Hello' }
    return '$p, $name!'
}

// Function with multiple return values
fn get_user_stats(users []User) (int, int) {
    mut adult_count := 0
    for user in users {
        if user.is_adult() {
            adult_count++
        }
    }
    return users.len, adult_count
}

// Generic function
fn find_user<T>(users []T, name string) ?T {
    for user in users {
        if user.name == name {
            return user
        }
    }
    return none
}

// Function with error handling
fn validate_user(user User) ! {
    if user.name.len == 0 {
        return error('Name cannot be empty')
    }
    if user.age < 0 {
        return error('Age cannot be negative')
    }
}

// Function using arrays
fn process_users(users []User) []string {
    return users.map(fn (u User) string {
        return u.str()
    })
}

// Function with mutable parameters
fn update_user(mut user User, name string, age int) ! {
    if age < 0 {
        return error('Age cannot be negative')
    }
    user.name = name
    user.age = age
}

// Function using channels
fn process_user_async(user User, ch chan string) {
    ch <- if user.is_adult() {
        'Adult: $user.name'
    } else {
        'Minor: $user.name'
    }
}

// Function using maps
struct UserRegistry {
mut:
    users map[string]User
}

fn new_registry() UserRegistry {
    return UserRegistry{
        users: map[string]User{}
    }
}

fn (mut r UserRegistry) add_user(user User) {
    r.users[user.name] = user
}

fn (r UserRegistry) get_user(name string) ?User {
    return r.users[name] or { none }
}

// Main function
fn main() {
    // Create users
    user1 := new_user('John', 25) or {
        println('Error creating user: $err')
        return
    }
    user2 := new_user('Alice', 17) or {
        println('Error creating user: $err')
        return
    }
    users := [user1, user2]
    
    // Test basic functions
    println('Users:')
    for user in users {
        println(user.str())
    }
    
    // Test processing
    println('\nProcessing results:')
    for user in users {
        result := user.process() or {
            println('Error: $err')
            continue
        }
        println('$user.name: $result')
    }
    
    // Test user stats
    total, adult_count := get_user_stats(users)
    println('\nStats:')
    println('Total users: $total')
    println('Adult users: $adult_count')
    
    // Test user finding
    println('\nFinding user:')
    found := find_user(users, 'John') or {
        println('User not found')
        User{}
    }
    println('Found: $found')
    
    // Test user registry
    mut registry := new_registry()
    for user in users {
        registry.add_user(user)
    }
    println('\nRegistry lookup:')
    if user := registry.get_user('John') {
        println(user.str())
    }
    
    // Test async processing
    ch := chan string{}
    println('\nAsync processing:')
    go process_user_async(user1, ch)
    go process_user_async(user2, ch)
    for _ in 0 .. 2 {
        result := <-ch
        println(result)
    }
    
    // Test optional parameters
    println('\nGreetings:')
    println(create_greeting('Bob'))
    println(create_greeting('Charlie', prefix: 'Hi'))
    
    // Test mutable updates
    mut test_user := user1
    update_user(mut test_user, 'John Doe', 26) or {
        println('Error updating user: $err')
        return
    }
    println('\nUpdated user:')
    println(test_user.str())
} 