"""Build a minimal Chinook-compatible SQLite DB for offline demos."""

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "chinook_mini.db"


def build_mini_chinook(db_path: Path = DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE Artist (ArtistId INTEGER PRIMARY KEY, Name NVARCHAR(120));
        CREATE TABLE Album (
            AlbumId INTEGER PRIMARY KEY,
            Title NVARCHAR(160) NOT NULL,
            ArtistId INTEGER NOT NULL,
            FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId)
        );
        CREATE TABLE Genre (GenreId INTEGER PRIMARY KEY, Name NVARCHAR(120));
        CREATE TABLE MediaType (MediaTypeId INTEGER PRIMARY KEY, Name NVARCHAR(120));
        CREATE TABLE Track (
            TrackId INTEGER PRIMARY KEY,
            Name NVARCHAR(200) NOT NULL,
            AlbumId INTEGER,
            MediaTypeId INTEGER NOT NULL,
            GenreId INTEGER,
            Composer NVARCHAR(220),
            Milliseconds INTEGER NOT NULL,
            Bytes INTEGER,
            UnitPrice NUMERIC(10,2) NOT NULL,
            FOREIGN KEY (AlbumId) REFERENCES Album(AlbumId),
            FOREIGN KEY (MediaTypeId) REFERENCES MediaType(MediaTypeId),
            FOREIGN KEY (GenreId) REFERENCES Genre(GenreId)
        );
        CREATE TABLE Employee (
            EmployeeId INTEGER PRIMARY KEY,
            LastName NVARCHAR(20) NOT NULL,
            FirstName NVARCHAR(20) NOT NULL,
            Title NVARCHAR(30),
            Email NVARCHAR(60)
        );
        CREATE TABLE Customer (
            CustomerId INTEGER PRIMARY KEY,
            FirstName NVARCHAR(40) NOT NULL,
            LastName NVARCHAR(20) NOT NULL,
            Company NVARCHAR(80),
            Address NVARCHAR(70),
            City NVARCHAR(40),
            State NVARCHAR(40),
            Country NVARCHAR(40),
            PostalCode NVARCHAR(10),
            Phone NVARCHAR(24),
            Fax NVARCHAR(24),
            Email NVARCHAR(60) NOT NULL,
            SupportRepId INTEGER,
            FOREIGN KEY (SupportRepId) REFERENCES Employee(EmployeeId)
        );
        CREATE TABLE Invoice (
            InvoiceId INTEGER PRIMARY KEY,
            CustomerId INTEGER NOT NULL,
            InvoiceDate DATETIME NOT NULL,
            BillingAddress NVARCHAR(70),
            BillingCity NVARCHAR(40),
            BillingState NVARCHAR(40),
            BillingCountry NVARCHAR(40),
            BillingPostalCode NVARCHAR(10),
            Total NUMERIC(10,2) NOT NULL,
            FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
        );
        CREATE TABLE InvoiceLine (
            InvoiceLineId INTEGER PRIMARY KEY,
            InvoiceId INTEGER NOT NULL,
            TrackId INTEGER NOT NULL,
            UnitPrice NUMERIC(10,2) NOT NULL,
            Quantity INTEGER NOT NULL,
            FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId),
            FOREIGN KEY (TrackId) REFERENCES Track(TrackId)
        );
        """
    )

    cur.execute("INSERT INTO MediaType VALUES (1, 'MPEG audio file')")
    cur.executemany(
        "INSERT INTO Genre VALUES (?, ?)",
        [(1, "Rock"), (2, "Jazz"), (3, "Metal"), (4, "Classical")],
    )
    cur.executemany(
        "INSERT INTO Artist VALUES (?, ?)",
        [
            (1, "The Rolling Stones"),
            (2, "Metallica"),
            (3, "Queen"),
            (4, "AC/DC"),
        ],
    )
    cur.executemany(
        "INSERT INTO Album VALUES (?, ?, ?)",
        [
            (1, "Hot Rocks, 1964-1971 (Disc 1)", 1),
            (2, "No Security", 1),
            (3, "Voodoo Lounge", 1),
            (4, "Black Album", 2),
            (5, "A Night at the Opera", 3),
            (6, "Back in Black", 4),
        ],
    )

    tracks = [
        (1, "Gimme Shelter", 1, 1, 1, 270000, 0.99),
        (2, "Sympathy For The Devil", 1, 1, 1, 380000, 0.99),
        (3, "Paint It Black", 1, 1, 1, 210000, 0.99),
        (4, "Jumpin' Jack Flash", 2, 1, 1, 220000, 0.99),
        (5, "Love Is Strong", 3, 1, 1, 230000, 0.99),
        (6, "Enter Sandman", 4, 1, 3, 330000, 0.99),
        (7, "Nothing Else Matters", 4, 1, 3, 388000, 0.99),
        (8, "Bohemian Rhapsody", 5, 1, 1, 354000, 0.99),
        (9, "Back in Black", 6, 1, 1, 255000, 0.99),
        (10, "You Can't Always Get What You Want", 1, 1, 1, 448000, 0.99),
    ]
    cur.executemany(
        "INSERT INTO Track (TrackId, Name, AlbumId, MediaTypeId, GenreId, Milliseconds, Bytes, UnitPrice) "
        "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
        tracks,
    )

    cur.execute(
        "INSERT INTO Employee VALUES (3, 'Peacock', 'Jane', 'Sales Support Agent', 'jane@chinookcorp.com')"
    )
    # Matches the handout phone number used in test case 1
    cur.execute(
        """
        INSERT INTO Customer VALUES (
            1, 'Luís', 'Gonçalves', 'Embraer - Empresa Brasileira de Aeronáutica S.A.',
            'Av. Brigadeiro Faria Lima, 2170', 'São José dos Campos', 'SP', 'Brazil', '12227-000',
            '+55 (12) 3923-5555', '+55 (12) 3923-5566', 'luisg@embraer.com.br', 3
        )
        """
    )
    cur.execute(
        """
        INSERT INTO Customer VALUES (
            2, 'Leonie', 'Köhler', NULL, 'Theodor-Heuss-Straße 34', 'Stuttgart', NULL,
            'Germany', '70174', '+49 0711 2842222', NULL, 'leonekohler@surfeu.de', 3
        )
        """
    )

    cur.executemany(
        "INSERT INTO Invoice VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, 1, "2023-05-01 00:00:00", "Av. Brigadeiro Faria Lima, 2170",
             "São José dos Campos", "SP", "Brazil", "12227-000", 3.96),
            (2, 1, "2024-01-15 00:00:00", "Av. Brigadeiro Faria Lima, 2170",
             "São José dos Campos", "SP", "Brazil", "12227-000", 5.94),
            (3, 1, "2025-08-07 00:00:00", "Av. Brigadeiro Faria Lima, 2170",
             "São José dos Campos", "SP", "Brazil", "12227-000", 8.91),
            (4, 2, "2024-06-10 00:00:00", "Theodor-Heuss-Straße 34",
             "Stuttgart", None, "Germany", "70174", 1.98),
        ],
    )
    cur.executemany(
        "INSERT INTO InvoiceLine VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1, 1, 0.99, 1),
            (2, 1, 2, 0.99, 1),
            (3, 1, 3, 0.99, 1),
            (4, 1, 4, 0.99, 1),
            (5, 2, 5, 0.99, 2),
            (6, 2, 6, 0.99, 2),
            (7, 2, 7, 0.99, 2),
            (8, 3, 1, 0.99, 3),
            (9, 3, 8, 0.99, 3),
            (10, 3, 10, 0.99, 3),
            (11, 4, 9, 0.99, 2),
        ],
    )

    conn.commit()
    conn.close()
    return db_path


if __name__ == "__main__":
    path = build_mini_chinook()
    print(f"Created {path}")
