
import os
import html

import bleach
import markdown
from dotenv import load_dotenv
from flask import Flask, render_template, request
from google import genai

load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "POST":

            claim = (request.form.get("health_claim") or "").strip()

            if not claim:
                return render_template(
                    "result.html",
                    analysis=html.escape("Please enter a health claim to analyse.")
                )

            prompt = f"""
You are HealthLens, an AI-powered educational health literacy assistant.

Your primary role is to help users think critically about health information—not to determine whether a claim is true or false.

The analysis should be educational, balanced, and objective.

Important guidelines:

• Do not present yourself as the final authority on scientific evidence.
• Do not fabricate concerns for well-established health concepts.
• If a claim is generally consistent with commonly recognized health knowledge, acknowledge this naturally and provide relevant context where appropriate.
• If a claim appears uncertain, exaggerated, controversial, or involves treatment of serious medical conditions, explain why additional evaluation may be appropriate.
• Avoid definitive statements unless they reflect widely recognized health knowledge, and present them as educational context rather than formal scientific verification.
• Never label a claim as "verified", "false", or "debunked".
• Maintain a professional and educational tone while adapting the depth of analysis to the nature of the claim.
• The target audience is the general public, not scientists or healthcare professionals. Use simple language and briefly explain scientific terms when they are necessary. Avoid writing like an academic review article.

Health Claim:
{claim}

Provide your response using the following headings.

### Claim Category
Identify the type of health claim (e.g., nutrition, treatment, prevention, diagnosis, lifestyle, wellness, supplement, or public health).

### Context
Provide a brief explanation of this specific claim and the relevant health context in 2-3 sentences.

Focus on helping a general user understand:
• Why this claim may appear believable or where the idea may come from.
• What important context is needed to interpret the claim properly.

Do not provide a detailed scientific overview. Do not explain every possible mechanism or background concept unless it is necessary to understand the claim.

If the claim relates to well-established health information, provide the relevant context without overstating uncertainty. If the topic is uncertain or still developing, explain that appropriately.

### Points for Critical Evaluation
Identify any important aspects of this specific claim that may require careful interpretation.

Focus on the reasoning behind the claim, including possible assumptions, limitations, missing context, or ways in which health information may be misunderstood.

Relevant considerations may include:
• Whether the claim presents a complex health topic as having a simple explanation or solution.
• Whether the claim makes a connection between two things without considering other possible explanations.
• Whether the claim depends on assumptions that may need further clarification.
• Whether findings from a specific context, such as laboratory studies, individual experiences, or preliminary research, are being applied more broadly than they may represent.
• Whether important factors such as dosage, timing, population differences, or individual variation may influence how the claim should be understood.
• Whether the wording of the claim creates confusion about the level of certainty, effectiveness, or applicability.

These are examples of possible considerations, not a checklist. Select only the points that are genuinely useful for explaining the specific claim.

Only include considerations that are genuinely relevant to the specific claim. If the claim does not contain meaningful concerns, focus on providing useful context rather than creating unnecessary doubt.

Explain these points as ways to understand and evaluate health information, not as a definitive scientific judgment by HealthLens.

Choose only the 2–3 most important considerations for this specific claim. Do not discuss every possible limitation.

### Questions to Explore
Provide 2-3 thoughtful questions that would help someone better understand or evaluate this claim.

### Further Sources to Explore
Explain what type of evidence would be useful for evaluating this specific claim and where a user can explore reliable information further.

Consider appropriate evidence types depending on the claim, such as:
• Randomized controlled trials for treatment-related claims.
• Systematic reviews and meta-analyses for overall evidence assessment.
• Long-term observational studies for population health claims.
• Clinical guidelines or recommendations from recognized health organizations.

Suggest relevant sources where users can explore this information, such as:
• Scientific databases.
• Government health agencies.
• Recognized health organizations.
• Professional medical organizations.

Do not imply that HealthLens has personally verified the claim using these sources.
Do not invent specific studies, papers, or citations.
Present these as resources for further learning and independent evaluation.
These are examples of possible considerations, not a checklist. Select only the sources that are more relevant forexplaining the specific claim.

### Key Takeaway
Summarize the most important educational message in two or three sentences. Encourage critical thinking without implying that every claim is equally uncertain.

### Disclaimer
HealthLens is an AI-assisted educational prototype developed to promote health literacy. The analysis is generated using a language model's general knowledge and reasoning capabilities. It is intended to support learning and critical evaluation and should not be interpreted as a definitive scientific assessment or as a substitute for advice from qualified healthcare professionals.

Maintain a professional, educational, and easy-to-understand writing style.
Keep the explanations concise and focused. Prioritize the most important 2–4 points rather than discussing every possible limitation.
Maintain a professional but conversational style suitable for someone without a scientific background.
Prefer clear explanations over technical terminology. When technical terms are necessary, briefly explain them in simple words.
Avoid unnecessary scientific jargon.
When explaining health claims, prioritize the user's understanding of the main idea rather than explaining every scientific mechanism behind it.
Do not introduce technical biological concepts unless they are necessary to understand why a claim should be interpreted carefully.
If a scientific term is used, explain it using simple everyday language.
"""

            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                return render_template(
                    "result.html",
                    analysis=html.escape(
                        "HealthLens is not configured correctly. Please check the API key."
                    )
                )

            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt
                )

                if not response.text:
                    raise ValueError("The Gemini API returned an empty response.")

                html_analysis = markdown.markdown(
                    response.text,
                    extensions=["extra", "nl2br"]
                )

                allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
                    "p", "h1", "h2", "h3", "h4",
                    "ul", "ol", "li",
                    "blockquote", "pre", "code",
                    "table", "thead", "tbody",
                    "tr", "th", "td",
                    "hr", "br"
                })

                safe_analysis = bleach.clean(
                    html_analysis,
                    tags=allowed_tags,
                    attributes={"a": ["href", "title"]},
                    protocols={"http", "https", "mailto"},
                    strip=True
                )

                return render_template(
                    "result.html",
                    analysis=safe_analysis
                )

            except Exception:
                app.logger.exception("HealthLens Gemini request failed.")

                return render_template(
                    "result.html",
                    analysis=html.escape(
                        "Sorry, HealthLens could not generate an analysis right now. Please try again later."
                    )
                )

        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/how-it-works")
    def how_it_works():
        return render_template("how_it_works.html")

    return app


app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
