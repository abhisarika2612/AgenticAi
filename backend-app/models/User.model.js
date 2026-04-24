// DEFINES WHAT A USER LOOKS LIKE IN THE DATABASE
// In-memory storage for simplicity (no database needed)

const users = new Map(); // Stores all users

class UserModel {
  static create(loginId, loginType) {
    const userId = Date.now().toString();
    const user = {
      id: userId,
      loginId: loginId,
      loginType: loginType,
      profile: {
        name: '',
        birthDate: '',
        grade: '',
        avatar: '1'
      },
      streak: 0,
      createdAt: new Date()
    };
    users.set(userId, user);
    return user;
  }
  
  static findByLoginId(loginId) {
    for (let user of users.values()) {
      if (user.loginId === loginId) {
        return user;
      }
    }
    return null;
  }
  
  static findById(userId) {
    return users.get(userId);
  }
  
  static update(userId, updates) {
    const user = users.get(userId);
    if (user) {
      Object.assign(user, updates);
      users.set(userId, user);
    }
    return user;
  }
  
  static getAllUsers() {
    return Array.from(users.values());
  }
}

module.exports = UserModel;