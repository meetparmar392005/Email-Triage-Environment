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
    if action.action_type != "classify":
        return 0.0, f"Wrong action_type '{action.action_type}', expected 'classify'"

    answer = action.value.lower().strip()
    domain = email.get("sender", "").split("@")[-1]
    is_spam = domain in SPAM_DOMAINS

    spam_words = {"spam", "junk", "phishing", "scam", "fraudulent"}
    legit_words = {"not_spam", "not spam", "legitimate", "ham", "legit", "real"}

    if is_spam and any(w in answer for w in spam_words):
        return 1.0, "Correct: spam identified"
    if not is_spam and any(w in answer for w in legit_words):
        return 1.0, "Correct: legitimate email identified"

    correct = "spam" if is_spam else "not_spam"
    return 0.2, f"Incorrect. Expected '{correct}', got '{answer}'"


def grade_prioritize(action, email) -> tuple:
    if action.action_type != "prioritize":
        return 0.0, f"Wrong action_type '{action.action_type}', expected 'prioritize'"

    answer = action.value.lower().strip()
    expected = email.get("expected_priority", "medium")

    if answer not in PRIORITY_SCORES:
        return 0.1, f"Invalid level '{answer}'. Use: critical / high / medium / low"

    if answer == expected:
        return 1.0, f"Correct priority: {expected}"

    diff = abs(PRIORITY_SCORES[answer] - PRIORITY_SCORES[expected])
    score = round(max(0.0, 1.0 - diff * 0.4), 2)
    return score, f"Expected '{expected}', got '{answer}' — partial credit"


def _keywords(text: str) -> list:
    stopwords = {"the", "a", "is", "in", "it", "of", "and", "to", "i",
                 "you", "we", "for", "on", "at", "hi", "hello"}
    words = [w.strip(".,?!") for w in text.lower().split() if len(w) > 3]
    return [w for w in words if w not in stopwords][:10]


def grade_reply(action, email) -> tuple:
    if action.action_type != "reply":
        return 0.0, f"Wrong action_type '{action.action_type}', expected 'reply'"

    reply = action.value.strip()
    if not reply:
        return 0.0, "Empty reply"
    if len(reply) < 20:
        return 0.1, "Reply too short to be useful"

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
    topic_score = min(0.4, matched * 0.1)
    score += topic_score
    if topic_score > 0:
        reasons.append(f"references {matched} relevant topic(s)")

    vague = {"ok", "sure", "okay", "noted", "alright"}
    if reply.lower().strip() not in vague and len(reply.split()) > 5:
        score += 0.2
        reasons.append("substantive response")

    return round(min(1.0, score), 2), "; ".join(reasons) or "minimal reply"


# ── Task class ────────────────────────────────────────────────────────────────

class Task:
    def __init__(self, task_id, email_pool, grader_fn, instructions):
        self.task_id = task_id
        self.email_pool = email_pool
        self.grader_fn = grader_fn
        self.instructions = instructions

    def sample_email(self) -> dict:
        return random.choice(self.email_pool)

    def grade(self, action, email) -> tuple:
        return self.grader_fn(action, email)


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
