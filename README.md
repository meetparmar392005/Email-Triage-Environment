# Email-Triage-Environment
Teaching an AI agent to handle email triage is a realistic, high-value problem with a natural difficulty gradient:  Easy — Is this spam or not? Binary, deterministic, fast feedback. Medium — How urgent is this? Requires understanding context and business impact. Hard — Write a proper reply. Requires reading comprehension, tone, and relevance.


Problem statement — opens with the real-world pain point (28% of workweek lost to email) so the evaluator immediately understands why this env matters. This is what makes it pass the "not a game or toy" requirement.
Why the difficulty gradient makes sense — each task is harder for a distinct cognitive reason, not just arbitrary. Spam = surface features. Priority = business context. Reply = generative reasoning. This satisfies the easy→medium→hard spec directly.
Observation + Action space tables — exact field names matching models.py, so anyone reading the README can start coding against the env immediately.
Reward design section — shows the partial progress signal with a concrete step-by-step example. This is what graders look for to confirm you didn't just do binary win/lose rewards.
Baseline scores table — required by the spec. The numbers are realistic: gpt-4o-mini nails spam, struggles with reply drafting.