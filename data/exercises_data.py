# egzersiz listesi ve MET katsayilari
# kalori hesabi: MET x kilo x sure(saat)
EXERCISES = [
    # Kardiyo
    {"name": "Yürüyüş (3.5 km/s)",          "category": "Kardiyo", "met": 2.8,  "icon": "directions_walk"},
    {"name": "Yürüyüş (5 km/s)",            "category": "Kardiyo", "met": 3.5,  "icon": "directions_walk"},
    {"name": "Hızlı yürüyüş (6.5 km/s)",    "category": "Kardiyo", "met": 5.0,  "icon": "directions_walk"},
    {"name": "Hafif koşu (8 km/s)",         "category": "Kardiyo", "met": 8.3,  "icon": "directions_run"},
    {"name": "Orta tempo koşu (10 km/s)",   "category": "Kardiyo", "met": 9.8,  "icon": "directions_run"},
    {"name": "Hızlı koşu (12 km/s)",        "category": "Kardiyo", "met": 11.5, "icon": "directions_run"},
    {"name": "Sprint koşusu",               "category": "Kardiyo", "met": 23.0, "icon": "bolt"},
    {"name": "Bisiklet (hafif, 16 km/s)",   "category": "Kardiyo", "met": 4.0,  "icon": "directions_bike"},
    {"name": "Bisiklet (orta, 20 km/s)",    "category": "Kardiyo", "met": 6.8,  "icon": "directions_bike"},
    {"name": "Bisiklet (hızlı, 25+ km/s)",  "category": "Kardiyo", "met": 10.0, "icon": "directions_bike"},
    {"name": "Statik bisiklet (kolay)",     "category": "Kardiyo", "met": 5.5,  "icon": "directions_bike"},
    {"name": "Statik bisiklet (orta)",      "category": "Kardiyo", "met": 7.0,  "icon": "directions_bike"},
    {"name": "Statik bisiklet (zor)",       "category": "Kardiyo", "met": 10.5, "icon": "directions_bike"},
    {"name": "Eliptik (orta)",              "category": "Kardiyo", "met": 5.0,  "icon": "directions_run"},
    {"name": "Eliptik (yoğun)",             "category": "Kardiyo", "met": 8.0,  "icon": "directions_run"},
    {"name": "Kürek makinası (orta)",       "category": "Kardiyo", "met": 7.0,  "icon": "rowing"},
    {"name": "Kürek makinası (yoğun)",      "category": "Kardiyo", "met": 8.5,  "icon": "rowing"},
    {"name": "Stair climber (merdiven)",    "category": "Kardiyo", "met": 8.0,  "icon": "stairs"},
    {"name": "İp atlama (orta tempo)",      "category": "Kardiyo", "met": 12.0, "icon": "bolt"},
    {"name": "İp atlama (hızlı)",           "category": "Kardiyo", "met": 12.3, "icon": "bolt"},

    # Göğüs
    {"name": "Bench press (yatay)",         "category": "Göğüs",   "met": 6.0,  "icon": "fitness_center"},
    {"name": "Bench press (eğimli/incline)","category": "Göğüs",   "met": 6.0,  "icon": "fitness_center"},
    {"name": "Bench press (düz/decline)",   "category": "Göğüs",   "met": 6.0,  "icon": "fitness_center"},
    {"name": "Dumbbell press (yatay)",      "category": "Göğüs",   "met": 5.0,  "icon": "fitness_center"},
    {"name": "Dumbbell press (eğimli)",     "category": "Göğüs",   "met": 5.0,  "icon": "fitness_center"},
    {"name": "Dumbbell fly",                "category": "Göğüs",   "met": 4.5,  "icon": "fitness_center"},
    {"name": "Cable crossover",             "category": "Göğüs",   "met": 4.5,  "icon": "fitness_center"},
    {"name": "Pec deck (machine fly)",      "category": "Göğüs",   "met": 3.5,  "icon": "fitness_center"},
    {"name": "Şınav (push-up)",             "category": "Göğüs",   "met": 3.8,  "icon": "self_improvement"},
    {"name": "Diamond push-up",             "category": "Göğüs",   "met": 4.5,  "icon": "self_improvement"},
    {"name": "Decline push-up",             "category": "Göğüs",   "met": 4.0,  "icon": "self_improvement"},
    {"name": "Dips (göğüs odaklı)",         "category": "Göğüs",   "met": 5.0,  "icon": "fitness_center"},

    # Sırt
    {"name": "Pull-up (geniş tutuş)",       "category": "Sırt",    "met": 8.0,  "icon": "fitness_center"},
    {"name": "Chin-up (dar tutuş)",         "category": "Sırt",    "met": 8.0,  "icon": "fitness_center"},
    {"name": "Lat pulldown",                "category": "Sırt",    "met": 5.0,  "icon": "fitness_center"},
    {"name": "Seated cable row",            "category": "Sırt",    "met": 5.0,  "icon": "fitness_center"},
    {"name": "Barbell row (bent-over)",     "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Dumbbell row (tek kol)",      "category": "Sırt",    "met": 5.5,  "icon": "fitness_center"},
    {"name": "T-bar row",                   "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Face pull",                   "category": "Sırt",    "met": 4.0,  "icon": "fitness_center"},
    {"name": "Deadlift (klasik)",           "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Deadlift (sumo)",             "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Romanian deadlift (RDL)",     "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Rack pull",                   "category": "Sırt",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Good morning",                "category": "Sırt",    "met": 5.0,  "icon": "fitness_center"},
    {"name": "Hyperextension (bel)",        "category": "Sırt",    "met": 3.5,  "icon": "fitness_center"},

    # Omuz
    {"name": "Overhead press (barbell)",    "category": "Omuz",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Military press",              "category": "Omuz",    "met": 6.0,  "icon": "fitness_center"},
    {"name": "Dumbbell shoulder press",     "category": "Omuz",    "met": 5.0,  "icon": "fitness_center"},
    {"name": "Arnold press",                "category": "Omuz",    "met": 5.0,  "icon": "fitness_center"},
    {"name": "Lateral raise (yan)",         "category": "Omuz",    "met": 3.5,  "icon": "fitness_center"},
    {"name": "Front raise (ön)",            "category": "Omuz",    "met": 3.5,  "icon": "fitness_center"},
    {"name": "Rear delt fly (arka)",        "category": "Omuz",    "met": 3.5,  "icon": "fitness_center"},
    {"name": "Upright row",                 "category": "Omuz",    "met": 4.5,  "icon": "fitness_center"},
    {"name": "Shrug (trapez)",              "category": "Omuz",    "met": 4.0,  "icon": "fitness_center"},
    {"name": "Pike push-up",                "category": "Omuz",    "met": 4.5,  "icon": "self_improvement"},
    {"name": "Handstand push-up",           "category": "Omuz",    "met": 8.0,  "icon": "self_improvement"},

    # Bacak & Kalça
    {"name": "Back squat (barbell)",        "category": "Bacak & Kalça", "met": 6.0,  "icon": "fitness_center"},
    {"name": "Front squat",                 "category": "Bacak & Kalça", "met": 6.0,  "icon": "fitness_center"},
    {"name": "Goblet squat",                "category": "Bacak & Kalça", "met": 5.0,  "icon": "fitness_center"},
    {"name": "Hack squat (machine)",        "category": "Bacak & Kalça", "met": 6.0,  "icon": "fitness_center"},
    {"name": "Leg press",                   "category": "Bacak & Kalça", "met": 5.5,  "icon": "fitness_center"},
    {"name": "Leg extension",               "category": "Bacak & Kalça", "met": 4.0,  "icon": "fitness_center"},
    {"name": "Leg curl (yatık)",            "category": "Bacak & Kalça", "met": 4.0,  "icon": "fitness_center"},
    {"name": "Leg curl (oturarak)",         "category": "Bacak & Kalça", "met": 4.0,  "icon": "fitness_center"},
    {"name": "Lunges (yürüyen)",            "category": "Bacak & Kalça", "met": 4.5,  "icon": "directions_walk"},
    {"name": "Reverse lunge",               "category": "Bacak & Kalça", "met": 4.5,  "icon": "directions_walk"},
    {"name": "Bulgarian split squat",       "category": "Bacak & Kalça", "met": 5.0,  "icon": "fitness_center"},
    {"name": "Calf raise (ayakta)",         "category": "Bacak & Kalça", "met": 3.5,  "icon": "fitness_center"},
    {"name": "Calf raise (oturarak)",       "category": "Bacak & Kalça", "met": 3.5,  "icon": "fitness_center"},
    {"name": "Hip thrust",                  "category": "Bacak & Kalça", "met": 5.5,  "icon": "fitness_center"},
    {"name": "Glute bridge",                "category": "Bacak & Kalça", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Step-up (kutu/bench)",        "category": "Bacak & Kalça", "met": 5.0,  "icon": "stairs"},
    {"name": "Jump squat (patlayıcı)",      "category": "Bacak & Kalça", "met": 7.0,  "icon": "bolt"},
    {"name": "Pistol squat",                "category": "Bacak & Kalça", "met": 7.0,  "icon": "self_improvement"},

    # Kol
    {"name": "Barbell curl",                "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Dumbbell curl",               "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Hammer curl",                 "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Preacher curl",               "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Cable curl",                  "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Concentration curl",          "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Tricep dips",                 "category": "Kol",     "met": 5.0,  "icon": "fitness_center"},
    {"name": "Tricep pushdown (cable)",     "category": "Kol",     "met": 3.5,  "icon": "fitness_center"},
    {"name": "Skull crusher",               "category": "Kol",     "met": 4.0,  "icon": "fitness_center"},
    {"name": "Overhead tricep extension",   "category": "Kol",     "met": 3.8,  "icon": "fitness_center"},
    {"name": "Close-grip bench press",      "category": "Kol",     "met": 5.5,  "icon": "fitness_center"},
    {"name": "Wrist curl (bilek)",          "category": "Kol",     "met": 3.0,  "icon": "fitness_center"},

    # Karın & Core
    {"name": "Plank (klasik)",              "category": "Karın & Core", "met": 3.5,  "icon": "self_improvement"},
    {"name": "Side plank (yan)",            "category": "Karın & Core", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Reverse plank",               "category": "Karın & Core", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Crunch (klasik)",             "category": "Karın & Core", "met": 3.8,  "icon": "self_improvement"},
    {"name": "Reverse crunch",              "category": "Karın & Core", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Oblique crunch (yan)",        "category": "Karın & Core", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Russian twist",               "category": "Karın & Core", "met": 4.5,  "icon": "self_improvement"},
    {"name": "Bicycle crunch",              "category": "Karın & Core", "met": 4.5,  "icon": "self_improvement"},
    {"name": "Leg raise (yerde)",           "category": "Karın & Core", "met": 4.5,  "icon": "self_improvement"},
    {"name": "Hanging leg raise (askıda)",  "category": "Karın & Core", "met": 5.5,  "icon": "fitness_center"},
    {"name": "Mekik (sit-up)",              "category": "Karın & Core", "met": 4.5,  "icon": "self_improvement"},
    {"name": "Mountain climber",            "category": "Karın & Core", "met": 8.0,  "icon": "bolt"},
    {"name": "V-up",                        "category": "Karın & Core", "met": 4.5,  "icon": "self_improvement"},
    {"name": "Dead bug",                    "category": "Karın & Core", "met": 3.5,  "icon": "self_improvement"},
    {"name": "Bird dog",                    "category": "Karın & Core", "met": 3.5,  "icon": "self_improvement"},
    {"name": "Ab wheel rollout",            "category": "Karın & Core", "met": 5.0,  "icon": "self_improvement"},
    {"name": "Hollow hold",                 "category": "Karın & Core", "met": 4.0,  "icon": "self_improvement"},

    # Fonksiyonel / HIIT
    {"name": "Burpee",                      "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "Box jump",                    "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "Jumping jack",                "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "Kettlebell swing",            "category": "Fonksiyonel / HIIT", "met": 7.5,  "icon": "fitness_center"},
    {"name": "Kettlebell snatch",           "category": "Fonksiyonel / HIIT", "met": 9.0,  "icon": "fitness_center"},
    {"name": "Kettlebell clean & jerk",     "category": "Fonksiyonel / HIIT", "met": 9.0,  "icon": "fitness_center"},
    {"name": "Battle ropes",                "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "Farmer's walk (ağır taşıma)", "category": "Fonksiyonel / HIIT", "met": 6.0,  "icon": "directions_walk"},
    {"name": "Sled push (kızak itme)",      "category": "Fonksiyonel / HIIT", "met": 9.0,  "icon": "fitness_center"},
    {"name": "Bear crawl",                  "category": "Fonksiyonel / HIIT", "met": 6.0,  "icon": "pets"},
    {"name": "Crossfit WOD",                "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "HIIT (yüksek yoğunluk)",      "category": "Fonksiyonel / HIIT", "met": 8.0,  "icon": "bolt"},
    {"name": "Tabata (4 dk yüksek tempo)",  "category": "Fonksiyonel / HIIT", "met": 10.0, "icon": "bolt"},

    # Yoga / Pilates
    {"name": "Hatha yoga (yavaş)",          "category": "Yoga / Pilates", "met": 2.5,  "icon": "self_improvement"},
    {"name": "Vinyasa yoga (akış)",         "category": "Yoga / Pilates", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Power yoga (yoğun)",          "category": "Yoga / Pilates", "met": 4.0,  "icon": "self_improvement"},
    {"name": "Hot yoga (Bikram)",           "category": "Yoga / Pilates", "met": 6.0,  "icon": "self_improvement"},
    {"name": "Pilates (mat)",               "category": "Yoga / Pilates", "met": 3.0,  "icon": "self_improvement"},
    {"name": "Pilates (reformer)",          "category": "Yoga / Pilates", "met": 3.5,  "icon": "self_improvement"},
    {"name": "Tai Chi",                     "category": "Yoga / Pilates", "met": 3.0,  "icon": "self_improvement"},

    # Esneklik
    {"name": "Statik esneme",               "category": "Esneklik", "met": 2.3,  "icon": "self_improvement"},
    {"name": "Dinamik esneme",              "category": "Esneklik", "met": 3.0,  "icon": "self_improvement"},
    {"name": "Foam rolling (myofascial)",   "category": "Esneklik", "met": 2.0,  "icon": "self_improvement"},
    {"name": "Mobility drill",              "category": "Esneklik", "met": 2.8,  "icon": "self_improvement"},

    # Takım Sporları
    {"name": "Futbol (maç)",                "category": "Takım Sporları", "met": 7.0,  "icon": "sports_soccer"},
    {"name": "Futbol (antrenman)",          "category": "Takım Sporları", "met": 7.0,  "icon": "sports_soccer"},
    {"name": "Basketbol (maç)",             "category": "Takım Sporları", "met": 8.0,  "icon": "sports_basketball"},
    {"name": "Basketbol (antrenman)",       "category": "Takım Sporları", "met": 6.5,  "icon": "sports_basketball"},
    {"name": "Voleybol",                    "category": "Takım Sporları", "met": 4.0,  "icon": "sports_volleyball"},
    {"name": "Hentbol",                     "category": "Takım Sporları", "met": 8.0,  "icon": "sports_handball"},
    {"name": "Rugby",                       "category": "Takım Sporları", "met": 8.3,  "icon": "sports_rugby"},

    # Raket Sporları
    {"name": "Tenis (tekli)",               "category": "Raket Sporları", "met": 7.3,  "icon": "sports_tennis"},
    {"name": "Tenis (çift)",                "category": "Raket Sporları", "met": 5.0,  "icon": "sports_tennis"},
    {"name": "Badminton",                   "category": "Raket Sporları", "met": 5.5,  "icon": "sports_tennis"},
    {"name": "Squash",                      "category": "Raket Sporları", "met": 12.0, "icon": "sports_tennis"},
    {"name": "Masa tenisi",                 "category": "Raket Sporları", "met": 4.0,  "icon": "sports_tennis"},
    {"name": "Padel",                       "category": "Raket Sporları", "met": 6.0,  "icon": "sports_tennis"},

    # Dövüş Sporları
    {"name": "Boks (torba)",                "category": "Dövüş Sporları", "met": 5.5,  "icon": "sports_mma"},
    {"name": "Boks (sparring)",             "category": "Dövüş Sporları", "met": 9.0,  "icon": "sports_mma"},
    {"name": "Kickbox",                     "category": "Dövüş Sporları", "met": 10.0, "icon": "sports_mma"},
    {"name": "Muay Thai",                   "category": "Dövüş Sporları", "met": 10.3, "icon": "sports_mma"},
    {"name": "MMA antrenmanı",              "category": "Dövüş Sporları", "met": 10.3, "icon": "sports_mma"},
    {"name": "Karate",                      "category": "Dövüş Sporları", "met": 10.3, "icon": "sports_mma"},
    {"name": "Taekwondo",                   "category": "Dövüş Sporları", "met": 10.3, "icon": "sports_mma"},
    {"name": "Judo",                        "category": "Dövüş Sporları", "met": 10.3, "icon": "sports_mma"},
    {"name": "BJJ (Brazilian Jiu-Jitsu)",   "category": "Dövüş Sporları", "met": 10.0, "icon": "sports_mma"},

    # Dans
    {"name": "Zumba",                       "category": "Dans",    "met": 6.5,  "icon": "music_note"},
    {"name": "Modern dans",                 "category": "Dans",    "met": 4.8,  "icon": "music_note"},
    {"name": "Hip-hop dans",                "category": "Dans",    "met": 6.0,  "icon": "music_note"},
    {"name": "Salsa",                       "category": "Dans",    "met": 5.5,  "icon": "music_note"},
    {"name": "Bale",                        "category": "Dans",    "met": 6.8,  "icon": "music_note"},
    {"name": "Halk oyunları",               "category": "Dans",    "met": 5.5,  "icon": "music_note"},

    # Su Sporları
    {"name": "Yüzme (serbest, orta)",       "category": "Su Sporları", "met": 6.0,  "icon": "pool"},
    {"name": "Yüzme (serbest, hızlı)",      "category": "Su Sporları", "met": 9.8,  "icon": "pool"},
    {"name": "Yüzme (sırtüstü)",            "category": "Su Sporları", "met": 4.8,  "icon": "pool"},
    {"name": "Yüzme (kelebek)",             "category": "Su Sporları", "met": 13.8, "icon": "pool"},
    {"name": "Yüzme (kurbağa)",             "category": "Su Sporları", "met": 10.3, "icon": "pool"},
    {"name": "Aqua aerobik",                "category": "Su Sporları", "met": 5.5,  "icon": "pool"},
    {"name": "Sutopu",                      "category": "Su Sporları", "met": 10.0, "icon": "pool"},
    {"name": "Kürek (açık su)",             "category": "Su Sporları", "met": 7.0,  "icon": "rowing"},

    # Doğa / Outdoor
    {"name": "Yürüyüş (köpek gezdirme)",    "category": "Doğa / Outdoor", "met": 3.0,  "icon": "pets"},
    {"name": "Doğa yürüyüşü (trekking)",    "category": "Doğa / Outdoor", "met": 6.0,  "icon": "hiking"},
    {"name": "Hiking (yüklü, sırt çantalı)","category": "Doğa / Outdoor", "met": 7.5,  "icon": "hiking"},
    {"name": "Trail running (patika koşu)", "category": "Doğa / Outdoor", "met": 9.0,  "icon": "directions_run"},
    {"name": "Dağcılık",                    "category": "Doğa / Outdoor", "met": 8.0,  "icon": "hiking"},
    {"name": "Bisiklet (dağ, off-road)",    "category": "Doğa / Outdoor", "met": 8.5,  "icon": "directions_bike"},
    {"name": "Kayak (alpine)",              "category": "Doğa / Outdoor", "met": 5.3,  "icon": "downhill_skiing"},
    {"name": "Snowboard",                   "category": "Doğa / Outdoor", "met": 5.3,  "icon": "snowboarding"},
    {"name": "Kaya tırmanışı",              "category": "Doğa / Outdoor", "met": 8.0,  "icon": "hiking"},
]


def get_categories():
    # kategori listesi, eklenme sirasiyla
    seen = []
    for ex in EXERCISES:
        if ex["category"] not in seen:
            seen.append(ex["category"])
    return seen


def get_by_category(category):
    # secilen kategorideki hareketler
    return [ex for ex in EXERCISES if ex["category"] == category]


def find_by_name(name):
    # tam ad eslesmesiyle hareket bulur
    for ex in EXERCISES:
        if ex["name"] == name:
            return ex
    return None


def calculate_calories(met, weight_kg, duration_min):
    # yakilan kalori = MET x kilo x sure(saat)
    return int(round(met * weight_kg * (duration_min / 60.0)))
