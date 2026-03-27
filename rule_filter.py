import json
import os

def load_schemes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "schemes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _derive_auto_flags(profile):
    """
    Derives implicit flags from the base profile attributes to make matching perfect
    without requiring the user to manually pass obvious flags.
    """
    flags = set(f.lower() for f in profile.get("flags", []))
    
    # Base attributes safe fetching
    age = profile.get("age", 0)
    income = profile.get("income", 9999999)
    gender = profile.get("gender", "").lower()
    caste = profile.get("caste", "").lower()
    religion = profile.get("religion", "").lower()
    occupation = profile.get("occupation", "").lower()

    if occupation:
        flags.add(occupation)

    # 1. Gender-based
    if gender == "female":
        flags.update(["woman", "any_woman_or_girl_child", "female"])
        if income <= 300000:
            flags.add("bpl_family_bride")
        if caste in ["kapu", "balija", "telaga", "ontari"]:
            flags.add("kapu_community_women")
    elif gender == "male":
        flags.add("man")

    # 2. Age-based
    if age >= 60:
        flags.add("senior_citizen")

    # 3. Income-based (EWS/BPL)
    if income <= 300000:
        flags.update(["economically_weaker", "bpl_family", "bpl", "bpl_family_bride"])

    # 4. Caste-based
    if caste == "sc":
        flags.add("sc_community")
    elif caste == "st":
        flags.add("st_community")
    elif caste in ["bc", "ebc"]:
        flags.add("bc_community")

    # 5. Religion-based (Minorities)
    if religion in ["muslim", "christian", "sikh", "buddhist", "parsi", "jain"]:
        flags.add("minority")
        if occupation == "student":
            flags.add("minority_student")

    # 6. Occupation-based specific mappings
    if occupation == "student":
        flags.add("student")
        if age <= 18:
            flags.add("school_student")
    elif occupation in ["tailor", "washerman", "barber"]:
        flags.add("traditional_artisans")
    elif occupation in ["driver", "auto_driver", "taxi_driver"]:
        flags.add("commercial_vehicle_owner_driver")
    elif occupation == "unemployed":
        # Treating unemployed as potentially a graduate or diploma holder for broad matching
        flags.update(["unemployed_graduate", "diploma_holder"])

    return flags


def rule_filter(user_profile):
    schemes = load_schemes()
    matched = []
    rejected = []

    # Pre-process profile variables to lowercase only once for O(1) matching & O(N) filtering efficiency
    u_age = user_profile.get("age", 0)
    u_income = user_profile.get("income", 9999999)
    u_gender = user_profile.get("gender", "").lower()
    u_caste = user_profile.get("caste", "").lower()
    u_religion = user_profile.get("religion", "").lower()
    u_occupation = user_profile.get("occupation", "").lower()
    
    # Auto-derive flags to implicitly match new fields perfectly
    u_flags = _derive_auto_flags(user_profile)

    for scheme in schemes:
        reasons_out = []

        # Age check
        min_age = scheme.get("min_age", 0)
        max_age = scheme.get("max_age", 999)
        if u_age < min_age:
            reasons_out.append(f"Age too low (min {min_age})")
        elif u_age > max_age:
            reasons_out.append(f"Age too high (max {max_age})")

        # Income check
        max_income = scheme.get("max_income", 9999999)
        if u_income > max_income:
            reasons_out.append(f"Income too high (max ₹{max_income:,})")

        # Gender check
        s_genders = [g.lower() for g in scheme.get("eligible_gender", [])]
        if "any" not in s_genders and u_gender not in s_genders:
            reasons_out.append(f"Gender not eligible (needs {scheme.get('eligible_gender')})")

        # Caste check
        s_castes = [c.lower() for c in scheme.get("eligible_caste", [])]
        if "any" not in s_castes and u_caste not in s_castes:
            reasons_out.append(f"Caste not eligible (needs {scheme.get('eligible_caste')})")

        # Religion check
        s_religions = [r.lower() for r in scheme.get("eligible_religion", [])]
        if "any" not in s_religions and u_religion not in s_religions:
            reasons_out.append(f"Religion not eligible (needs {scheme.get('eligible_religion')})")

        # Occupation check
        s_occupations = [o.lower() for o in scheme.get("eligible_occupation", [])]
        if "any" not in s_occupations and u_occupation not in s_occupations:
            reasons_out.append(f"Occupation not eligible (needs {scheme.get('eligible_occupation')})")

        # Special flags check
        s_flags = [f.lower() for f in scheme.get("eligible_for", [])]
        if "any" not in s_flags:
            # Efficient set intersection Check
            if not u_flags.intersection(set(s_flags)):
                reasons_out.append(f"Special eligibility not met (needs one of {scheme.get('eligible_for')})")

        if not reasons_out:
            matched.append(scheme)
        else:
            rejected.append({"scheme": scheme.get("name"), "reasons": reasons_out})

    return matched, rejected


def format_matched(matched):
    if not matched:
        return "No schemes matched your profile."
    lines = []
    for s in matched:
        lines.append(f"✅ {s['name']} ({s['category']})")
        lines.append(f"   Benefit: {s['benefits']}")
        lines.append(f"   Apply at: {s['apply_at']}")
        lines.append("")
    return "\n".join(lines)


# ── Quick test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_profile = {
        "age": 22,
        "gender": "female",
        "caste": "BC",
        "religion": "Muslim",
        "occupation": "student",
        "income": 180000,
        "flags": []
    }

    print("=== Testing Rule Filter ===")
    print(f"Profile: {test_profile}\n")

    matched, rejected = rule_filter(test_profile)

    print(f"MATCHED ({len(matched)} schemes):")
    print(format_matched(matched))

    print(f"REJECTED ({len(rejected)} schemes):")
    for r in rejected:
        print(f"  ❌ {r['scheme']}: {', '.join(r['reasons'])}")