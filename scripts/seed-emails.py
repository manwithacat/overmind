"""Send sample emails to Stalwart via SMTP for PoC demonstration."""
import json
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path


def main():
    emails = json.loads((Path(__file__).parent / "seed-data" / "emails.json").read_text())

    # Wait for Stalwart to be ready
    for attempt in range(30):
        try:
            with smtplib.SMTP("stalwart", 25, timeout=5) as smtp:
                smtp.ehlo()
                break
        except (ConnectionRefusedError, OSError):
            print(f"Waiting for Stalwart... (attempt {attempt + 1}/30)")
            time.sleep(2)
    else:
        raise RuntimeError("Stalwart not available after 60 seconds")

    # Send each email
    with smtplib.SMTP("stalwart", 25) as smtp:
        for i, email_data in enumerate(emails):
            msg = MIMEText(email_data["body"])
            msg["Subject"] = email_data["subject"]
            msg["From"] = email_data["from"]
            msg["To"] = email_data["to"]
            if "cc" in email_data:
                msg["Cc"] = email_data["cc"]

            recipients = [email_data["to"]]
            if "cc" in email_data:
                recipients.append(email_data["cc"])

            smtp.sendmail(email_data["from"], recipients, msg.as_string())
            print(f"Sent email {i + 1}/{len(emails)}: {email_data['subject']}")
            time.sleep(0.5)

    print(f"Done! Sent {len(emails)} seed emails.")


if __name__ == "__main__":
    main()
