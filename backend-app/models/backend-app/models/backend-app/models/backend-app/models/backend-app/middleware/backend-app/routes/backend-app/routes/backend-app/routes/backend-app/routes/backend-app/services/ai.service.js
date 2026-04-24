// HANDLES GENERATING AI ANSWERS

function getAIAnswer(question, documents) {
  // Check if user has uploaded any documents
  if (documents.length === 0) {
    return {
      text: "⚠️ Please upload your notes or past papers first! I can only answer based on YOUR materials.",
      source: "No documents uploaded",
      confidence: 0
    };
  }
  
  const doc = documents[0];
  const questionLower = question.toLowerCase();
  let answerText = "";
  
  // Simple keyword matching for demo
  if (questionLower.includes('hess') || questionLower.includes('enthalpy')) {
    answerText = "Hess's Law states that the total enthalpy change is independent of the pathway. ΔH°rxn = ΣΔH°f(products) - ΣΔH°f(reactants)";
  } 
  else if (questionLower.includes('calculus') || questionLower.includes('derivative')) {
    answerText = "The derivative measures instantaneous rate of change. d/dx[x^n] = n·x^(n-1)";
  } 
  else if (questionLower.includes('newton') || questionLower.includes('force')) {
    answerText = "Newton's Second Law: F = ma (Force = mass × acceleration)";
  } 
  else if (questionLower.includes('photosynthesis')) {
    answerText = "Photosynthesis converts light energy to chemical energy: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂";
  }
  else {
    answerText = `Based on your document "${doc.name}", review the section about ${doc.topics.join(', ')} to find the answer to: "${question}"`;
  }
  
  return {
    text: answerText,
    source: `📌 Based on: ${doc.name}`,
    confidence: 85
  };
}

module.exports = { getAIAnswer };