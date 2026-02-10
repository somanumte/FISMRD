from app.services.icecat_service import IcecatService
import re

def test_logic():
    test_cases = [
        {
            "brand": "Lenovo",
            "family": "ThinkPad",
            "series": "T Series",
            "name": "ThinkPad T14s 2-in-1 Gen 1",
            "code": "21M1000CUS",
            "expected": "ThinkPad T14s 2-in-1 Gen 1"
        },
        {
            "brand": "DELL",
            "family": "Latitude",
            "series": "3000",
            "name": "3550",
            "code": "N004L355015EMEA_VP",
            "expected": "Latitude 3550"
        },
        {
            "brand": "ASUS",
            "family": "ROG",
            "series": "Strix G16",
            "name": "G614FR-TS344",
            "code": "G614FR-TS344",
            "expected": "ROG Strix G16 G614FR-TS344"
        },
        {
            "brand": "MSI",
            "family": "Gaming",
            "series": "GF63",
            "name": "Gaming GF63 12VE-009XES Thin",
            "code": "GF63-12VE-009XES",
            "expected": "Gaming GF63 12VE-009XES Thin"
        },
        {
            "brand": "MSI",
            "family": "Cyborg",
            "series": "Cyborg 15",
            "name": "Cyborg 15 B2RWFKG-421US",
            "code": "B2RWFKG-421US",
            "expected": "Cyborg 15 B2RWFKG-421US"
        },
        {
            "brand": "Samsung",
            "family": "Galaxy Book",
            "series": "Book5 Pro",
            "name": "Galaxy Book5 Pro 360 (16\", Core Ultra 5, 16GB)",
            "code": "NP960XGK-KC1US",
            "expected": "Galaxy Book5 Pro 360 (16\", Core Ultra 5, 16GB)"
        },
        {
            "brand": "Apple",
            "family": "MacBook Air",
            "series": "(M4, 2025)",
            "name": "MacBook Air",
            "code": "MC214LL/A",
            "expected": "MacBook Air (M4, 2025)"
        },
        {
            "brand": "HP",
            "family": "ENVY x360",
            "series": "15-ed0000",
            "name": "15-ed0021nia",
            "code": "204M7EA",
            "expected": "ENVY x360 15-ed0021nia"
        },
        {
            "brand": "Gigabyte",
            "family": "Gaming",
            "series": "G5",
            "name": "KF-E3ES313SD",
            "code": "KF-E3ES313SD",
            "expected": "Gaming KF-E3ES313SD"
        },
        {
            "brand": "Samsung",
            "family": "Galaxy Book5 360",
            "series": "Book5",
            "name": "Pro",
            "code": "NP960XGK",
            "expected": "Galaxy Book5 360 Pro"
        }
    ]

    with open("tests/final_results.txt", "w", encoding="utf-8") as f:
        f.write(f"{'BRAND':<10} | {'EXPECTED':<45} | {'RESULT':<45} | {'STATUS'}\n")
        f.write("-" * 110 + "\n")
        
        for case in test_cases:
            result = IcecatService._build_model_name(
                case["brand"],
                case["family"],
                case["series"],
                case["name"],
                case["code"]
            )
            status = "✅ PASS" if result == case["expected"] else "❌ FAIL"
            line = f"{case['brand']:<10} | {case['expected']:<45} | {result:<45} | {status}\n"
            f.write(line)
            print(line, end="")
            if result != case["expected"]:
                f.write(f"   Details: F={case['family']}, S={case['series']}, N={case['name']}, C={case['code']}\n")

if __name__ == "__main__":
    test_logic()
