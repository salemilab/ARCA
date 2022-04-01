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

def getRegionIds(db):
    regs = []
    for row in db.execute("SELECT subregion, country FROM Countries WHERE code='S' ORDER BY idx;").fetchall():
        regs.append(row)
    return regs

def getCountryName(db, countryid):
    return db.execute("SELECT country FROM Countries WHERE idx=?;", (countryid,)).fetchone()[0]

def getCases(db, countryid, virus_ids, start_year, start_week, end_year, end_week):
    v = ",".join(virus_ids)
    query = "SELECT year, week, virus, cases FROM Cases WHERE virus IN (" + v + ") AND country=? AND year >= ? AND year <= ? ORDER BY year, week;"
    return db.execute(query, (countryid, start_year, end_year)).fetchall()

def getSummaryData(db):
    data = {}
    virus_names = []
    
    virus_ids = getViruses(db)
    for vir in virus_ids:
        vid = vir[0]
        vn = db.execute("SELECT virus FROM viruses WHERE idx=?", (vid,)).fetchone()[0]
        virus_names.append(vn)
        initial = db.execute("SELECT min(year) FROM Cases WHERE virus=?;", (vid,)).fetchone()[0]
        final   = db.execute("SELECT max(year) FROM Cases WHERE virus=?;", (vid,)).fetchone()[0]
        data[vn + "_i"] = initial
        data[vn + "_f"] = final
        cases = db.execute("SELECT sum(cases) FROM Cases a, Countries b WHERE a.country=b.idx and b.code='C' and virus=?;", (vid,)).fetchone()[0]
        data[vn + "_cases"] = "{:,}".format(cases)
    data["virus_names"] = virus_names
    data["viruses"] = ", ".join(virus_names)
    data["ncountries"] = db.execute("SELECT count(*) FROM Countries WHERE code='C';").fetchone()[0]

    tablerows = ""
    regions = getRegionIds(db)
    for reg in regions:
        regcount = db.execute("select sum(cases) from Cases a, Countries b where a.country=b.idx and b.subregion=? and b.code='C';", (reg[0],)).fetchone()[0]
        row = "<TR><TD>{}</TD><TD class='w3-right'>{:,}</TD></TR>\n".format(reg[1], regcount)
        tablerows += row
    data["regcounts"] = tablerows
    return data

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
