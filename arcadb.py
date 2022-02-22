import sqlite3 as sql

def opendb():
    return sql.connect("arca.db")

def getViruses(db):
    result = db.execute("SELECT idx, virus FROM viruses ORDER BY idx;").fetchall()
    return result

def getVirusNames(db, virus_ids):
    results = []
    for vid in virus_ids:
        results.append(db.execute("SELECT virus FROM viruses WHERE idx=?", (vid,)).fetchone()[0])
    return results

def getStartYear(db):
    result = db.execute("SELECT min(year) FROM Cases;").fetchone()[0]
    return result

def getEndYear(db):
    result = db.execute("SELECT max(year) FROM Cases;").fetchone()[0]
    return result

def getCountries(db):
    return db.execute("SELECT idx, country FROM Countries WHERE code='C';").fetchall()

def getRegions(db):
    return db.execute("SELECT subregion, country FROM Countries WHERE code='S';").fetchall()

def getCountryName(db, countryid):
    return db.execute("SELECT country FROM Countries WHERE idx=?;", (countryid,)).fetchone()[0]

def getCases(db, countryid, virus_ids, start_year, start_week, end_year, end_week):
    v = ",".join(virus_ids)
    query = "SELECT year, week, virus, cases FROM Cases WHERE virus IN (" + v + ") AND country=? AND year >= ? AND year <= ? ORDER BY year, week;"
    return db.execute(query, (countryid, start_year, end_year)).fetchall()
    
# Classes

class FormData(object):
    viruses = []
    start_year = 0
    end_year = 0
    countries = []
    regions = []
    
    def load(self):
        db = opendb();
        try:
            self.viruses = getViruses(db)
            self.start_year = getStartYear(db)
            self.end_year = getEndYear(db)
            self.countries = getCountries(db)
            self.regions = getRegions(db)
        finally:
            db.close()
