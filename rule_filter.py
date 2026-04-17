import json
import os

def load_schemes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "schemes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _derive_auto_flags(profile):
    """
    Derives implicit eligibility flags from the user's base profile.
    All flag strings are lowercase for O(1) set-intersection matching.
    """
    flags = set(f.lower() for f in profile.get("flags", []))

    age            = profile.get("age", 0)
    income         = profile.get("income", 9999999)
    gender         = profile.get("gender", "").lower()
    caste          = profile.get("caste", "").lower()
    religion       = profile.get("religion", "").lower()
    occupation     = profile.get("occupation", "").lower()
    marital_status = profile.get("marital_status", "").lower()   # NEW
    residence_type = profile.get("residence_type", "").lower()   # NEW: "rural" | "urban"

    # ── Occupation base flag ──────────────────────────────────────────────
    if occupation:
        flags.add(occupation)

    # ── Gender ───────────────────────────────────────────────────────────
    if gender == "female":
        flags.update(["woman", "female", "any_woman_or_girl_child"])

        # Maternal flags
        if 18 <= age <= 45:
            flags.add("new_mother")
        if 19 <= age <= 45:
            flags.add("pregnant_woman")

        # Single / separated / deserted women pension
        if marital_status in ["single", "separated", "deserted", "unmarried"]:
            flags.add("single_woman")

        # BPL bride for marriage assistance
        if income <= 300000:
            flags.add("bpl_family_bride")

        # Kapu community women
        if caste in ["kapu", "balija", "telaga", "ontari"]:
            flags.add("kapu_community_women")

    elif gender == "male":
        flags.add("man")

    # ── Age ──────────────────────────────────────────────────────────────
    if age >= 60:
        flags.add("senior_citizen")

    # ── Income ───────────────────────────────────────────────────────────
    if income <= 300000:
        flags.update(["economically_weaker", "bpl_family", "bpl"])
    if income <= 144000:               # NTR Bharosa pension income ceiling
        flags.add("pension_eligible_income")

    # ── Caste ────────────────────────────────────────────────────────────
    if caste == "sc":
        flags.update(["sc_community", "sc_st_household"])
    elif caste == "st":
        flags.update(["st_community", "sc_st_household"])
    elif caste in ["bc", "ebc"]:
        flags.add("bc_community")
    elif caste in ["kapu", "balija", "telaga", "ontari"]:
        flags.add("kapu_community")

    # ── Religion ─────────────────────────────────────────────────────────
    minority_religions = {"muslim", "christian", "sikh", "buddhist", "parsi", "jain"}
    if religion in minority_religions:
        flags.add("minority")
        if occupation == "student":
            flags.add("minority_student")

    # ── Occupation-specific flags ─────────────────────────────────────────
    if occupation == "student":
        flags.add("student")
        if age <= 16:
            flags.add("school_student")

    elif occupation == "farmer":
        flags.add("farmer")
        # Tenant farmers also benefit from Annadata Sukhibhava
        flags.add("tenant_farmer")

    elif occupation in ["weaver"]:
        flags.update(["weaver", "weaver_owning_handloom"])

    elif occupation in ["fisherman", "fisher"]:
        flags.update(["fisherman", "active_fisherman", "boat_owner"])

    elif occupation in ["driver", "auto_driver", "taxi_driver", "auto"]:
        flags.update(["driver", "auto_driver", "taxi_driver",
                       "commercial_vehicle_owner_driver"])

    elif occupation in ["tailor", "washerman", "barber"]:
        flags.add("traditional_artisans")

    elif occupation in ["employee", "worker", "factory_worker",
                         "private_employee", "government_employee"]:
        flags.add("organised_sector_worker")

    elif occupation == "unemployed":
        flags.update(["unemployed_graduate", "diploma_holder"])

    # ── Residence type ────────────────────────────────────────────────────
    if residence_type == "rural":
        flags.add("rural_resident")
    elif residence_type == "urban":
        flags.update(["urban_resident", "urban"])

    # ── Houseless flag (explicit) ─────────────────────────────────────────
    if profile.get("houseless", False):
        flags.add("houseless")

    return flags


def rule_filter(user_profile):
    schemes = load_schemes()
    matched = []
    rejected = []

    u_age      = user_profile.get("age", 0)
    u_income   = user_profile.get("income", 9999999)
    u_gender   = user_profile.get("gender", "").lower()
    u_caste    = user_profile.get("caste", "").lower()
    u_religion = user_profile.get("religion", "").lower()
    u_occ      = user_profile.get("occupation", "").lower()

    u_flags = _derive_auto_flags(user_profile)

    for scheme in schemes:
        reasons_out = []

        # ── Age ──────────────────────────────────────────────────────────
        min_age = scheme.get("min_age", 0)
        max_age = scheme.get("max_age", 999)
        if u_age < min_age:
            reasons_out.append(f"Age too low (min {min_age})")
        elif u_age > max_age:
            reasons_out.append(f"Age too high (max {max_age})")

        # ── Income ───────────────────────────────────────────────────────
        max_income = scheme.get("max_income", 9999999)
        if u_income > max_income:
            reasons_out.append(f"Income too high (max ₹{max_income:,})")

        # ── Gender ───────────────────────────────────────────────────────
        s_genders = [g.lower() for g in scheme.get("eligible_gender", [])]
        if "any" not in s_genders and u_gender not in s_genders:
            reasons_out.append(f"Gender not eligible (needs {scheme.get('eligible_gender')})")

        # ── Caste ────────────────────────────────────────────────────────
        s_castes = [c.lower() for c in scheme.get("eligible_caste", [])]
        if "any" not in s_castes and u_caste not in s_castes:
            reasons_out.append(f"Caste not eligible (needs {scheme.get('eligible_caste')})")

        # ── Religion ─────────────────────────────────────────────────────
        s_religions = [r.lower() for r in scheme.get("eligible_religion", [])]
        if "any" not in s_religions and u_religion not in s_religions:
            reasons_out.append(f"Religion not eligible (needs {scheme.get('eligible_religion')})")

        # ── Occupation ───────────────────────────────────────────────────
        s_occs = [o.lower() for o in scheme.get("eligible_occupation", [])]
        if "any" not in s_occs and u_occ not in s_occs:
            # Secondary check: occupation may have been mapped to a flag
            occ_flags_match = u_flags.intersection(set(s_occs))
            if not occ_flags_match:
                reasons_out.append(
                    f"Occupation not eligible (needs {scheme.get('eligible_occupation')})"
                )

        # ── Special eligibility flags ─────────────────────────────────────
        s_flags = [f.lower() for f in scheme.get("eligible_for", [])]
        if "any" not in s_flags:
            if not u_flags.intersection(set(s_flags)):
                reasons_out.append(
                    f"Special eligibility not met (needs one of {scheme.get('eligible_for')})"
                )

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
        lines.append(f"   Benefit : {s['benefits']}")
        lines.append(f"   Apply at: {s['apply_at']}")
        lines.append("")
    return "\n".join(lines)


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test 1 — SC female farmer, rural, BPL
    test_profiles = [
        {
            "label": "SC female farmer, rural, BPL",
            "age": 35, "gender": "female", "caste": "SC",
            "religion": "Hindu", "occupation": "farmer",
            "income": 120000, "residence_type": "rural",
            "marital_status": "married", "houseless": False, "flags": []
        },
        {
            "label": "BC male student, Muslim, urban",
            "age": 20, "gender": "male", "caste": "BC",
            "religion": "Muslim", "occupation": "student",
            "income": 180000, "residence_type": "urban",
            "marital_status": "single", "houseless": False, "flags": []
        },
        {
            "label": "General female, widow, age 65, houseless",
            "age": 65, "gender": "female", "caste": "OC",
            "religion": "Hindu", "occupation": "none",
            "income": 0, "residence_type": "rural",
            "marital_status": "widowed", "houseless": True, "flags": ["widow"]
        },
        {
            "label": "ST male weaver, age 55",
            "age": 55, "gender": "male", "caste": "ST",
            "religion": "Hindu", "occupation": "weaver",
            "income": 96000, "residence_type": "rural",
            "marital_status": "married", "houseless": False, "flags": []
        },
    ]

    for profile in test_profiles:
        print(f"\n{'='*55}")
        print(f"Profile: {profile['label']}")
        print('='*55)
        matched, rejected = rule_filter(profile)
        print(f"MATCHED ({len(matched)}):")
        print(format_matched(matched))
        print(f"REJECTED ({len(rejected)}):")
        for r in rejected:
            print(f"  ❌ {r['scheme']}: {', '.join(r['reasons'])}")