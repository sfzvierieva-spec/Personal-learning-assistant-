"""Command-line demo: run a real course file through the whole pipeline.

    python -m ingestion_generation.demo path/to/course.pdf --format quiz --user A

Uses the fake users from profile_and_prompts' end-to-end test, so the same
course can be generated for two profiles and compared (--user A / B / C).
Needs ANTHROPIC_API_KEY in the environment.
"""

from __future__ import annotations

import argparse
import json

from profile_and_prompts.profile.builder import build_profile
from profile_and_prompts.prompt_generator.generator import generate_system_prompt
from profile_and_prompts.tests.test_end_to_end import FAKE_USERS

from . import SUPPORTED_FORMATS, extract_text, generate_content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("course", help="PDF, DOCX, TXT or MD file")
    parser.add_argument("--format", default="flashcards", choices=SUPPORTED_FORMATS + ["synthesis_sheet"])
    parser.add_argument("--user", default="A", choices=["A", "B", "C"])
    parser.add_argument("--num-items", type=int)
    parser.add_argument("--exam-date", help="YYYY-MM-DD (revision_plan)")
    parser.add_argument("--out", help="save the JSON result to this file")
    args = parser.parse_args()

    answers = next(a for name, a in FAKE_USERS.items() if name.startswith(f"User {args.user}"))
    system_prompt = generate_system_prompt(build_profile(answers))

    course_text = extract_text(args.course)
    context = {"num_items": args.num_items, "exam_date": args.exam_date}
    result = generate_content(course_text, system_prompt, args.format,
                              {k: v for k, v in context.items() if v})

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
