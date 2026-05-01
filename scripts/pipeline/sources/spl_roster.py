"""Curated current SPL club roster.

Used as a fallback whenever live scrapers (FBref, Wikidata) come back with
zero rows — usually because of a 403, a rate limit, or an upstream rename.
The names, founding years, and Wikidata QIDs below are stable across seasons,
so even a fully offline pipeline run produces a real-looking snapshot.

When the live sources do return data, they win — this list is only used to
fill gaps.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuratedClub:
    slug: str
    name_en: str
    name_ar: str
    short_en: str
    short_ar: str
    city_en: str
    city_ar: str
    founded: int
    primary_color: str
    wikidata_qid: str | None


# Long-standing top-flight clubs in the Saudi Pro League. Order roughly tracks
# historical league standing. Promotions/relegations happen, so consumers
# should still prefer live data when available.
SPL_CLUBS: tuple[CuratedClub, ...] = (
    CuratedClub("al-hilal", "Al-Hilal", "نادي الهلال", "Al-Hilal", "الهلال",
                "Riyadh", "الرياض", 1957, "#1E4FAD", "Q221054"),
    CuratedClub("al-nassr", "Al-Nassr", "نادي النصر", "Al-Nassr", "النصر",
                "Riyadh", "الرياض", 1955, "#FFCC00", "Q221055"),
    CuratedClub("al-ittihad", "Al-Ittihad", "نادي الاتحاد", "Al-Ittihad", "الاتحاد",
                "Jeddah", "جدة", 1927, "#000000", "Q221061"),
    CuratedClub("al-ahli", "Al-Ahli", "نادي الأهلي", "Al-Ahli", "الأهلي",
                "Jeddah", "جدة", 1937, "#007A33", "Q221060"),
    CuratedClub("al-shabab", "Al-Shabab", "نادي الشباب", "Al-Shabab", "الشباب",
                "Riyadh", "الرياض", 1947, "#FFFFFF", "Q221056"),
    CuratedClub("al-ettifaq", "Al-Ettifaq", "نادي الاتفاق", "Al-Ettifaq", "الاتفاق",
                "Dammam", "الدمام", 1944, "#C8102E", "Q221062"),
    CuratedClub("al-fateh", "Al-Fateh", "نادي الفتح", "Al-Fateh", "الفتح",
                "Al-Hasa", "الأحساء", 1958, "#7B2D8E", "Q1376094"),
    CuratedClub("al-taawoun", "Al-Taawoun", "نادي التعاون", "Al-Taawoun", "التعاون",
                "Buraidah", "بريدة", 1956, "#FFD600", "Q1373571"),
    CuratedClub("al-khaleej", "Al-Khaleej", "نادي الخليج", "Al-Khaleej", "الخليج",
                "Saihat", "سيهات", 1945, "#0033A0", "Q1525057"),
    CuratedClub("al-wehda", "Al-Wehda", "نادي الوحدة", "Al-Wehda", "الوحدة",
                "Mecca", "مكة", 1945, "#C8102E", "Q1373580"),
    CuratedClub("al-riyadh", "Al-Riyadh", "نادي الرياض", "Al-Riyadh", "الرياض",
                "Riyadh", "الرياض", 1954, "#FFFFFF", "Q1373574"),
    CuratedClub("al-fayha", "Al-Fayha", "نادي الفيحاء", "Al-Fayha", "الفيحاء",
                "Al Majma'ah", "المجمعة", 1957, "#3F2E78", "Q4663316"),
    CuratedClub("damac", "Damac", "نادي ضمك", "Damac", "ضمك",
                "Khamis Mushait", "خميس مشيط", 1972, "#1E5BA3", "Q1373577"),
    CuratedClub("al-qadsiah", "Al-Qadsiah", "نادي القادسية", "Al-Qadsiah", "القادسية",
                "Khobar", "الخبر", 1967, "#FFD600", "Q1373587"),
    CuratedClub("al-okhdood", "Al-Okhdood", "نادي الأخدود", "Al-Okhdood", "الأخدود",
                "Najran", "نجران", 1981, "#FFB800", "Q56276850"),
    CuratedClub("al-raed", "Al-Raed", "نادي الرائد", "Al-Raed", "الرائد",
                "Buraidah", "بريدة", 1954, "#FFCC00", "Q1373575"),
    CuratedClub("al-najma", "Al-Najma", "نادي النجمة", "Al-Najma", "النجمة",
                "Unayzah", "عنيزة", 1945, "#0033A0", "Q1373585"),
    CuratedClub("al-kholood", "Al-Kholood", "نادي الخلود", "Al-Kholood", "الخلود",
                "Ar Rass", "الرس", 1980, "#3F2E78", "Q104836970"),
)
