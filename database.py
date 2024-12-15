import aiosqlite

DATABASE_FILE = "pokemon_database.db"

# Initialize the database with tables for Pokémon, runs, and thresholds
async def initialize_database():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        # Create the runs table (stores run names and their generations)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                generation TEXT
            )
        """)
        
        # Create the pokemon table (stores pokemon details for each run)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                form TEXT,
                route TEXT,
                bst INTEGER,
                points INTEGER,
                status TEXT DEFAULT 'Alive',
                run TEXT,
                FOREIGN KEY (run) REFERENCES runs(name)
            )
        """)
        
        # Create the point thresholds table (stores BST thresholds and associated points)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS point_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                max_bst INTEGER,
                points INTEGER
            )
        """)
        
        # Insert default point thresholds if none exist
        await db.execute("""
            INSERT OR IGNORE INTO point_thresholds (max_bst, points)
            VALUES
            (200, 1),
            (300, 2),
            (400, 3),
            (9999, 4)
        """)
        
        # Create the active run table (stores the current active run)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_run (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        await db.commit()


# Add a new Pokémon to the database
async def add_pokemon(name, form, route, bst, points, run_name):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT INTO pokemon (name, form, route, bst, points, status, run)
            VALUES (?, ?, ?, ?, ?, 'Alive', ?)
        """, (name, form, route, bst, points, run_name))
        await db.commit()


# Fetch the currently active run
async def get_active_run():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        cursor = await db.execute("SELECT name FROM active_run LIMIT 1")
        result = await cursor.fetchone()
        return result[0] if result else None


# Select a run as the active run
async def select_run(run_name):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("DELETE FROM active_run")  # Clear any previous active run
        await db.execute("INSERT INTO active_run (name) VALUES (?)", (run_name,))
        await db.commit()


# Add a new run to the database
async def add_run(run_name, generation):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT INTO runs (name, generation)
            VALUES (?, ?)
        """, (run_name, generation))
        await db.commit()


# List all runs in the database
async def list_runs():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        cursor = await db.execute("SELECT name, generation FROM runs")
        return await cursor.fetchall()


# Fetch all Pokémon for a specific run
async def get_pokemon_by_run(run_name):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        cursor = await db.execute("""
            SELECT name, form, route, bst, points, status 
            FROM pokemon
            WHERE run = ?
        """, (run_name,))
        return await cursor.fetchall()


# Update the status of a Pokémon in a specific run
async def update_pokemon_status(name, run_name, new_status):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            UPDATE pokemon
            SET status = ?
            WHERE name = ? AND run = ?
        """, (new_status, name, run_name))
        await db.commit()


# Fetch all point thresholds from the database
async def get_thresholds():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        cursor = await db.execute("SELECT max_bst, points FROM point_thresholds ORDER BY max_bst")
        return await cursor.fetchall()


# Update a point threshold in the database
async def update_threshold(max_bst, points):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO point_thresholds (max_bst, points)
            VALUES (?, ?)
        """, (max_bst, points))
        await db.commit()


# Function to calculate point value based on the BST and thresholds
def calculate_point_value(bst, thresholds):
    for threshold in thresholds:
        max_bst, points = threshold
        if bst <= max_bst:
            return points
    return 0  # Default case, shouldn't happen if thresholds are properly defined
