import csv
import sqlite3

DB_PATH = "restaurants.db"
CSV_PATH = "restaurants.csv"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS 가게 (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                가게이름  TEXT    NOT NULL UNIQUE,
                휴무일    TEXT,
                주소      TEXT
            )
        """)
        conn.commit()


def insert_restaurant(가게이름: str, 휴무일: str, 주소: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO 가게 (가게이름, 휴무일, 주소) VALUES (?, ?, ?)",
            (가게이름, 휴무일, 주소),
        )
        conn.commit()


def get_all_restaurants():
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, 가게이름, 휴무일, 주소 FROM 가게")
        return cursor.fetchall()


def get_open_restaurants(today: str):
    """오늘 요일(예: '월', '화')이 휴무일이 아닌 가게 반환"""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, 가게이름, 주소 FROM 가게 WHERE 휴무일 NOT LIKE ?",
            (f"%{today}%",),
        )
        return cursor.fetchall()


def export_to_csv(csv_path: str = CSV_PATH):
    """DB의 가게 데이터를 CSV 파일로 저장"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, 가게이름, 휴무일, 주소 FROM 가게")
        rows = cursor.fetchall()

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "가게이름", "휴무일", "주소"])
        writer.writerows(rows)

    print(f"CSV 저장 완료: {csv_path} ({len(rows)}개 가게)")


if __name__ == "__main__":
    create_table()

    # 샘플 데이터 삽입
    sample_data = [
        ("남대갈뚝배기", "화요일", "울산 북구 송정16길 15"),
        ("경주잔치집", "수요일", "울산 북구 송정16길 8"),
        ("언양닭칼국수 송정점", "일요일", "울산 북구 송정14길 9"),
        ("송정매운어탕수제비", "월요일", "울산 북구 송정36길 6"),
        ("안가네오리&삼계탕", "토요일", "울산 북구 송정36길 5"),
        ("라오", "일요일", "울산 북구 송정15길 10"),
        ("왓더버거 송정점", None, "울산 북구 박상진11로 8"),
        ("부산정 북구송정점", "화요일", "울산 북구 화산로 123"),
        ("환장라멘 송정본점", "화요일", "울산 북구 송정17길 3"),
        ("롯데리아 송정점", None, "울산 북구 화산로 109"),
    ]
    for name, off, addr in sample_data:
        insert_restaurant(name, off, addr)

    print("전체 가게 목록:")
    for row in get_all_restaurants():
        print(row)

    print("\n월요일 영업 가게:")
    for row in get_open_restaurants("월"):
        print(row)

    export_to_csv()
