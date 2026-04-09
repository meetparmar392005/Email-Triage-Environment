import random

# ── Email corpus ──────────────────────────────────────────────────────────────

EMAILS = {
    "spam": [
        {
            "subject": "You've won $1,000,000!",
            "sender": "lucky@prize-winner.biz",
            "body": "Click here to claim your prize now! Limited time offer!",
            "timestamp": "2024-01-15T09:00:00",
        },
        {
            "subject": "Enlarge your profits NOW",
            "sender": "deals@spammy.xyz",
            "body": "Buy our miracle supplement and triple your income in 30 days!",
            "timestamp": "2024-01-15T09:05:00",
        },
        {
            "subject": "URGENT: Account suspended",
            "sender": "security@paypa1.fake",
            "body": "Your PayPal account is suspended. Verify now at http://phish.biz",
            "timestamp": "2024-01-15T09:10:00",
        },
    ],
    "legit": [
        {
            "subject": "Q3 report attached",
            "sender": "alice@company.com",
            "body": "Hi team, please find the Q3 financial report attached. Review before Friday's meeting.",
            "timestamp": "2024-01-15T10:00:00",
        },
        {
            "subject": "Interview scheduled for Tuesday",
            "sender": "hr@acme.com",
            "body": "Your interview is confirmed for Tuesday at 2pm. Please bring your portfolio.",
            "timestamp": "2024-01-15T10:15:00",
        },
        {
            "subject": "Bug report: login page broken",
            "sender": "bob@company.com",
            "body": "The login page returns a 500 error on Safari. Logs attached. Urgent fix needed.",
            "timestamp": "2024-01-15T11:00:00",
        },
    ],
    "mixed_priority": [
        {
            "subject": "Team lunch tomorrow",
            "sender": "carol@company.com",
            "body": "Just a reminder, team lunch is tomorrow at noon at the usual place.",
            "timestamp": "2024-01-15T12:00:00",
            "expected_priority": "low",
        },
        {
            "subject": "Server is down - production!",
            "sender": "alerts@monitoring.io",
            "body": "CRITICAL: Production server CPU at 100%, 503 errors spiking. Immediate attention required.",
            "timestamp": "2024-01-15T13:00:00",
            "expected_priority": "critical",
        },
        {
            "subject": "Please review my PR",
            "sender": "dave@company.com",
            "body": "Hi, I've opened a PR for the new user auth feature. Review when you get a chance.",
            "timestamp": "2024-01-15T14:00:00",
            "expected_priority": "medium",
        },
        {
            "subject": "Invoice #4521 due in 3 days",
            "sender": "billing@vendor.com",
            "body": "Your invoice of $4,200 is due on Friday. Please process payment to avoid late fees.",
            "timestamp": "2024-01-15T15:00:00",
            "expected_priority": "high",
        },
    ],
    "reply_needed": [
        {
            "subject": "Can we reschedule our meeting?",
            "sender": "eve@partner.com",
            "body": "Hi, I have a conflict on Thursday at 3pm. Could we move to Friday same time or Monday at 10am?",
            "timestamp": "2024-01-15T16:00:00",
        },
        {
            "subject": "Feedback on your proposal",
            "sender": "frank@client.com",
            "body": "Thanks for the proposal. We like the direction but have two concerns: timeline seems tight and we'd need dedicated support. Can you address these?",
            "timestamp": "2024-01-15T17:00:00",
        },
    ],
}

SPAM_DOMAINS = {"prize-winner.biz", "spammy.xyz", "paypa1.fake"}
PRIORITY_SCORES = {"critical": 4, "high": 3, "medium": 2, "low": 1}


# ── Graders ───────────────────────────────────────────────────────────────────

def grade_classify(action, email) -> tuple:
    """Grade classification action with robust error handling."""
    try:
        # Validate action type
        if not hasattr(action, 'action_type') or action.action_type != "classify":
            return 0.01, f"Wrong action_type '{getattr(action, 'action_type', 'None')}', expected 'classify'"

        # Validate action value
        if not hasattr(action, 'value') or action.value is None:
            return 0.01, "Missing action value"
        
        answer = str(action.value).lower().strip()
        if not answer:
            return 0.01, "Empty action value"
        
        # Safely extract domain
        sender = email.get("sender", "")
        if not sender or "@" not in sender:
            return 0.01, "Invalid email sender format"
        
        domain = sender.split("@")[-1]
        is_spam = domain in SPAM_DOMAINS
    except Exception as e:
        return 0.01, f"Error processing classification: {str(e)}"

    spam_words = {"spam", "junk", "phishing", "scam", "fraudulent"}
    legit_words = {"not_spam", "not spam", "legitimate", "ham", "legit", "real"}

    if is_spam and any(w in answer for w in spam_words):
        return 0.95, "Correct: spam identified"
    if not is_spam and any(w in answer for w in legit_words):
        return 0.95, "Correct: legitimate email identified"

    correct = "spam" if is_spam else "not_spam"
    return 0.2, f"Incorrect. Expected '{correct}', got '{answer}'"


def grade_prioritize(action, email) -> tuple:
    """Grade prioritization action with robust error handling."""
    try:
        # Validate action type
        if not hasattr(action, 'action_type') or action.action_type != "prioritize":
            return 0.01, f"Wrong action_type '{getattr(action, 'action_type', 'None')}', expected 'prioritize'"

        # Validate action value
        if not hasattr(action, 'value') or action.value is None:
            return 0.01, "Missing action value"
        
        answer = str(action.value).lower().strip()
        if not answer:
            return 0.01, "Empty action value"
        
        expected = email.get("expected_priority", "medium")
    except Exception as e:
        return 0.01, f"Error processing prioritization: {str(e)}"

    if answer not in PRIORITY_SCORES:
        return 0.1, f"Invalid level '{answer}'. Use: critical / high / medium / low"

    if answer == expected:
        return 0.95, f"Correct priority: {expected}"

    diff = abs(PRIORITY_SCORES[answer] - PRIORITY_SCORES[expected])
    score = round(max(0.01, 0.95 - diff * 0.3), 2)
    return score, f"Expected '{expected}', got '{answer}' — partial credit"


def _keywords(text: str) -> list:
    stopwords = {"the", "a", "is", "in", "it", "of", "and", "to", "i",
                 "you", "we", "for", "on", "at", "hi", "hello"}
    words = [w.strip(".,?!") for w in text.lower().split() if len(w) > 3]
    return [w for w in words if w not in stopwords][:10]


def grade_reply(action, email) -> tuple:
    """Grade reply action with robust error handling."""
    try:
        # Validate action type
        if not hasattr(action, 'action_type') or action.action_type != "reply":
            return 0.01, f"Wrong action_type '{getattr(action, 'action_type', 'None')}', expected 'reply'"

        # Validate action value
        if not hasattr(action, 'value') or action.value is None:
            return 0.01, "Missing action value"
        
        reply = str(action.value).strip()
        if not reply:
            return 0.01, "Empty reply"
        if len(reply) < 20:
            return 0.1, "Reply too short to be useful"
    except Exception as e:
        return 0.01, f"Error processing reply: {str(e)}"

    score = 0.0
    reasons = []

    if len(reply) >= 50:
        score += 0.2
        reasons.append("adequate length")

    greetings = {"hi", "hello", "dear", "thanks", "thank you", "appreciate"}
    if any(g in reply.lower() for g in greetings):
        score += 0.2
        reasons.append("has greeting/acknowledgment")

    key_topics = _keywords(email.get("body", ""))
    matched = sum(1 for kw in key_topics if kw in reply.lower())
    topic_score = min(0.35, matched * 0.1)
    score += topic_score
    if topic_score > 0:
        reasons.append(f"references {matched} relevant topic(s)")

    vague = {"ok", "sure", "okay", "noted", "alright"}
    if reply.lower().strip() not in vague and len(reply.split()) > 5:
        score += 0.2
        reasons.append("substantive response")

    # Ensure score is always in valid range (0.01, 0.99)
    final_score = round(min(0.95, max(0.01, score)), 2)
    return final_score, "; ".join(reasons) or "minimal reply"


# ── Task class ────────────────────────────────────────────────────────────────

class Task:
    def __init__(self, task_id, email_pool, grader_fn, instructions):
        self.task_id = task_id
        self.email_pool = email_pool
        self.grader_fn = grader_fn
        self.instructions = instructions

    def sample_email(self) -> dict:
        """Sample a random email from the pool with error handling."""
        try:
            if not self.email_pool:
                raise ValueError(f"Empty email pool for task '{self.task_id}'")
            return random.choice(self.email_pool)
        except Exception as e:
            # Return a default email if sampling fails
            return {
                "subject": "Error",
                "sender": "error@system.local",
                "body": f"Error sampling email: {str(e)}",
                "timestamp": "2024-01-15T00:00:00",
            }

    def grade(self, action, email) -> tuple:
        """Grade an action with error handling."""
        try:
            score, reason = self.grader_fn(action, email)
            # Ensure score is always in valid range (0.01, 0.99) - STRICTLY between 0 and 1
            score = float(score)
            score = min(0.99, max(0.01, score))
            return score, str(reason)
        except Exception as e:
            return 0.01, f"Grading error: {str(e)}"


# ── Task registry ─────────────────────────────────────────────────────────────

TASKS = {
    "easy": Task(
        task_id="easy",
        email_pool=EMAILS["spam"] + EMAILS["legit"],
        grader_fn=grade_classify,
        instructions=(
            "Classify this email as 'spam' or 'not_spam'. "
            "Set action_type='classify' and value to your answer."
        ),
    ),
    "medium": Task(
        task_id="medium",
        email_pool=EMAILS["mixed_priority"],
        grader_fn=grade_prioritize,
        instructions=(
            "Assign a priority level to this email. "
            "Choose from: critical / high / medium / low. "
            "Set action_type='prioritize' and value to your chosen level."
        ),
    ),
    "hard": Task(
        task_id="hard",
        email_pool=EMAILS["reply_needed"],
        grader_fn=grade_reply,
        instructions=(
            "Draft a professional reply to this email. Address the sender's request directly. "
            "Set action_type='reply' and value to your full reply text."
        ),
    ),
}
