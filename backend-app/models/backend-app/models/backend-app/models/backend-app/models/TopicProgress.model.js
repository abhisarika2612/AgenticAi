// TRACKS HOW WELL USER KNOWS EACH TOPIC

const userTopics = new Map(); // Stores topic progress per user

class TopicProgressModel {
  static updateProgress(userId, topic, isCorrect) {
    if (!userTopics.has(userId)) {
      userTopics.set(userId, new Map());
    }
    
    const userTopicMap = userTopics.get(userId);
    
    if (!userTopicMap.has(topic)) {
      userTopicMap.set(topic, { correct: 0, total: 0 });
    }
    
    const progress = userTopicMap.get(topic);
    progress.total += 1;
    if (isCorrect) progress.correct += 1;
    
    userTopicMap.set(topic, progress);
    userTopics.set(userId, userTopicMap);
    
    return progress;
  }
  
  static getProgress(userId) {
    const userTopicMap = userTopics.get(userId);
    if (!userTopicMap) return {};
    
    const result = {};
    for (let [topic, data] of userTopicMap) {
      result[topic] = data;
    }
    return result;
  }
}

module.exports = TopicProgressModel;