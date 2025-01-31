(* Module signature *)
module type UserManager = sig
  type user
  type 'a result = Ok of 'a | Error of string
  
  val create_user : string -> int -> user
  val process_user : user -> user result
  val get_name : user -> string
  val get_age : user -> int
  val format_user : user -> string
end

(* Module implementation *)
module User : UserManager = struct
  type user = {
    name: string;
    age: int;
  }

  type 'a result = Ok of 'a | Error of string

  (* Basic function *)
  let create_user name age =
    { name = name; age = age }

  (* Pattern matching function *)
  let process_user user =
    match user.age with
    | age when age < 0 -> Error "Invalid age"
    | age when age < 18 -> Error "Underage"
    | _ -> Ok user

  (* Record field accessor functions *)
  let get_name user = user.name
  let get_age user = user.age

  (* String formatting function *)
  let format_user user =
    Printf.sprintf "%s (%d years old)" user.name user.age
end

(* Function with labeled arguments *)
let update_user ~name ~age user =
  { user with User.name = name; age = age }

(* Higher-order function *)
let process_users f users =
  List.map f users

(* Function with optional argument *)
let create_greeting ?(prefix="Hello") name =
  prefix ^ ", " ^ name ^ "!"

(* Recursive function *)
let rec find_user name = function
  | [] -> None
  | user :: rest ->
      if User.get_name user = name then Some user
      else find_user name rest

(* Function using List module *)
let get_adult_users users =
  List.filter (fun user -> User.get_age user >= 18) users

(* Partial application *)
let is_adult = (>=) 18

(* Function composition *)
let get_uppercase_name user =
  user |> User.get_name |> String.uppercase_ascii

(* Function with local bindings *)
let process_and_format user =
  let open User in
  let result = process_user user in
  match result with
  | Ok processed -> "Success: " ^ format_user processed
  | Error msg -> "Error: " ^ msg

(* Curried function *)
let add_ages user1 user2 =
  User.get_age user1 + User.get_age user2

(* Main execution *)
let () =
  let user1 = User.create_user "John" 25 in
  let user2 = User.create_user "Alice" 17 in
  let users = [user1; user2] in

  (* Test basic functions *)
  Printf.printf "User 1: %s\n" (User.format_user user1);
  Printf.printf "User 2: %s\n" (User.format_user user2);

  (* Test processing *)
  let process_results = process_users User.process_user users in
  List.iter (function
    | Ok user -> Printf.printf "Processed: %s\n" (User.format_user user)
    | Error msg -> Printf.printf "Error: %s\n" msg
  ) process_results;

  (* Test higher-order functions *)
  let adult_users = get_adult_users users in
  Printf.printf "Adult users: %d\n" (List.length adult_users);

  (* Test optional arguments *)
  let greeting = create_greeting ~prefix:"Hi" "Bob" in
  Printf.printf "%s\n" greeting;

  (* Test partial application *)
  let is_user_adult user = is_adult (User.get_age user) in
  Printf.printf "Is user1 adult? %b\n" (is_user_adult user1);

  (* Test function composition *)
  let uppercase_name = get_uppercase_name user1 in
  Printf.printf "Uppercase name: %s\n" uppercase_name; 