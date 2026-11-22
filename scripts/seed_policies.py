from pathlib import Path
from app.db import get_supabase

POLICIES = [
    ("aura-anc-guide", "Aura ANC Headphones Guide", "troubleshooting", "policies/aura_anc_guide.md"),
    ("pulse-monitors-guide", "Pulse Studio Monitors Guide", "troubleshooting", "policies/pulse_monitors_guide.md"),
    ("warranty-and-returns", "Warranty, Missing Parts & Returns", "policy", "policies/warranty_and_returns.md"),
]


def main() -> None:
    print("Connecting to Supabase over HTTPS...")
    sb = get_supabase()
    for slug, title, category, filepath in POLICIES:
        content = Path(filepath).read_text(encoding="utf-8")
        sb.table("policy_docs").upsert(
            {"slug": slug, "title": title, "category": category, "content": content},
            on_conflict="slug",
        ).execute()
    print("Seeded 3 Lumen Audio policy documents into Supabase!")


if __name__ == "__main__":
    main()
