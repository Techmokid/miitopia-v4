userMemory = []

class memoryContainer:
    def __init__(self, username: str):
        self.username = username
        self.data_list = []

def clearUserData(username: str):
    global userMemory
    for user in userMemory:
        if user.username == username:
            user.data_list.clear()
            return
    print(f"Warning: User data for {username} not found")

def addUserData(username: str, data):
    global userMemory
    for user in userMemory:
        if user.username == username:
            if isinstance(data, list):
                user.data_list.extend(data)  # Efficient way to append a list
            else:
                user.data_list.append(data)
            return

    # User doesn't exist. Add to list
    newUser = memoryContainer(username)
    if isinstance(data, list):
        newUser.data_list = data  # Efficient way to append a list
    else:
        newUser.data_list = [data]
    userMemory.append(newUser)

def getUserData(username):
    global userMemory
    for user in userMemory:
        if user.username == username:
            return user.data_list
    userMemory.append(memoryContainer(username))
    return []

if __name__ == "__main__":
    import miitopiaV4
