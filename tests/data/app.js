function greet(name) {
    return `Hello, ${name}!`;
}

class UserService {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
    }
} 