interface User {
    id: number;
    name: string;
}

class UserManager {
    private users: User[] = [];
    
    public addUser(user: User): void {
        this.users.push(user);
    }
} 