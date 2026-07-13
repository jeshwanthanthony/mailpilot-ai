from openai import OpenAI

from app.config import Settings


class ReplyWriter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(
        self,
        sender: str,
        subject: str,
        email_body: str,
        tone: str,
        extra_instructions: str,
    ) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OpenAI is not configured")
        client = OpenAI(api_key=self.settings.openai_api_key, timeout=30.0, max_retries=2)
        input_text = "\n".join(
            [
                f"Tone: {tone}",
                f"Sender: {sender}",
                f"Subject: {subject}",
                f"Additional direction: {extra_instructions or 'None'}",
                "",
                "Email to answer:",
                email_body[:12_000],
            ]
        )
        response = client.responses.create(
            model=self.settings.openai_model,
            instructions=(
                "Write a natural email reply for the account owner. Address the request directly, "
                "avoid inventing commitments or facts, and return only the reply body without a "
                "subject or signature."
            ),
            input=input_text,
            max_output_tokens=500,
            store=False,
        )
        draft = response.output_text.strip()
        if not draft:
            raise RuntimeError("The model returned an empty draft")
        return draft
