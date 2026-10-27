# Кўп функцияли Telegram Бот (Instagram Downloader + File Converter)

Ушбу бот 2 та асосий функцияни бажаради:
1. **Instagram видео юклаш**: Reels, Post, IGTV ҳаволаси юборилганда видео файлни юклаб беради.
2. **Универсал файл конвертери**: Ҳар қандай файл (Excel, Расм, Аудио, Видео, Ҳужжат) юборилганда уни керакли янги форматга ўгириб беради.

---

## ☁️ Render.com сайтида 24/7 бепул ишга тушириш бўйича қўлланма

### 1-қадам: Render'да рўйхатдан ўтиш
1. [render.com](https://render.com/) сайтига киринг ва **GitHub** орқали рўйхатдан ўтинг (Sign in with GitHub).

### 2-қадам: Янги Web Service яратиш
1. Render бошқарув панелида **«New +»** ➔ **«Web Service»** тугмасини босинг.
2. **«Build and deploy from a Git repository»** ни танлаб, `Nasiba-instagram` репозиторийингизни танланг (Connect).

### 3-қадам: Созламаларни киритиш
- **Name**: `nasiba-instagram-bot`
- **Region**: Франкфурт (Frankfurt) ёки Сингапур
- **Branch**: `main`
- **Runtime**:
  - Агар **Docker** танланса: Бот учун FFmpeg ва Chromium автоматик ўрнатилади (Тавсия этилади).
  - Агар **Python** танланса:
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `python main.py`
- **Instance Type**: **Free** ($0/month)

### 4-қадам: Environment Variables (Муҳит ўзгарувчилари)
Пастдаги **«Environment Variables»** бўлимига қуйидаги ўзгарувчини қўшинг:

| Key (Калит) | Value (Қиймат) |
|---|---|
| `BOT_TOKEN` | Сизнинг Telegram @BotFather'дан олинган бот токенингиз |
| `PYTHON_VERSION` | `3.12.0` (Агар Python Runtime танланган бўлса) |

Ва ниҳоят пастдаги **«Deploy Web Service»** тугмасини босинг. Бот бир неча дақиқада тўлиқ ишга тушади!
