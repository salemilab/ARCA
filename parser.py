#!/usr/bin/env python3

import sys
import os.path
import sqlite3 as sql
from openpyxl import load_workbook

def opendb():
    return sql.connect("arca.db")

def get_excel_sheet(filename):
    wb = load_workbook(filename = filename)
    sheetname = wb.sheetnames[0]
    return wb[sheetname]

def convert_to_tab_delimited(filename):
    sh = get_excel_sheet(filename)

    for row in sh.rows:
        # Version 1:
        #for cell in row:
        #    sys.stdout.write(str(cell.value) + "\t")

        # Version 2:
        #sys.stdout.write(str(row[0].value))
        #for cell in row[1:]:
        #    sys.stdout.write("\t" + str(cell.value))
        #sys.stdout.write("\n")

        # Version 3:
        sys.stdout.write("\t".join([ str(c.value) for c in row ]) + "\n")

def store_countries(filename):
    sh = get_excel_sheet(filename)
    db = opendb()
    data = False
    savedid = 0
    success = False

    try:
        for row in sh.rows:
            if data:
                regid = row[0].value
                country = row[1].value
                if regid is None:
                    regid = savedid
                else:
                    savedid = regid
                db.execute("INSERT INTO Countries (subregion, country) VALUES (?, ?);", (regid, country))

            else:
                data = True
        success = True

    finally:
        if success:
            db.commit()
        db.close()

def get_country_id(db, country, regid):
    idx = db.execute("SELECT idx FROM Countries WHERE country=?", (country,)).fetchone()
    if idx:
        return idx[0]

    try:
        db.execute("INSERT INTO Countries (subregion, country) VALUES (?, ?);", (regid, country))
        db.commit()
        idx = db.execute("SELECT idx FROM Countries WHERE country=?", (country,)).fetchone()
        return idx[0]
    except:
        return None

def get_totalcases(db, virus, country, year, week):
    row = db.execute("SELECT totalcases FROM Cases WHERE virus=? AND country=? AND year=? AND week<? ORDER BY week DESC LIMIT 1;", (virus, country, year, week)).fetchone()
    if row:
        #sys.stderr.write("{}, {}: {}\n".format(country, year, row[0]))
        return row[0]
    else:
        #sys.stderr.write("{}, {}: empty\n".format(country, year))
        return 0

def get_virus_id(db, name):
    row = db.execute("SELECT idx FROM Viruses WHERE virus=?;", (name,)).fetchone()
    if row:
        return row[0]
    else:
        sys.stderr.write("Unknown virus: {}\n".format(name))
        sys.exit(1)

def get_year_week(filename):
    name = os.path.split(filename)[1]
    year = name[:4]
    week = name[9:11]
    return year, week

def parse_one_file(db, virus, filename):
    year, week = get_year_week(filename)
    sh = get_excel_sheet(filename)
    data = False
    success = False

    try:
        for row in sh.rows:
            if data:
                regid = row[0].value
                country = row[1].value
                countryid = get_country_id(db, country, regid)
                cases = row[6].value
                if cases is None:
                    totalcases = 0
                else:
                    totalcases = int(cases)
                prev_totalcases = get_totalcases(db, virus, countryid, year, week)
                newcases = totalcases - prev_totalcases
                db.execute("INSERT INTO Cases (country, virus, year, week, cases, totalcases) VALUES (?, ?, ?, ?, ?, ?);",
                           (countryid, virus, year, week, newcases, totalcases))
            else:
                data = True
        success = True

    finally:
        sys.stderr.write("Parsing {}: {}\n".format(filename, success))
        if success:
            db.commit()

def parse_monthly_file(db, virus, filename):
    sh = get_excel_sheet(filename)
    rn = 0
    success = False
    try:
        for row in sh.rows:
            if rn == 0:
                years = row
            elif rn == 1:
                weeks = row
            elif rn > 2:
                regid = row[0].value
                country = row[1].value
                countryid = get_country_id(db, country, regid)
                totalcases = 0
                
                for i in range(2, 55):
                    year = years[i].value
                    if year is None:
                        totalcases = 0
                    else:
                        week = weeks[i].value
                        newcases = row[i].value
                        if newcases is None:
                            continue
                        totalcases += newcases
                        db.execute("INSERT INTO Cases (country, virus, year, week, cases, totalcases) VALUES (?, ?, ?, ?, ?, ?);",
                                   (countryid, virus, year, week, newcases, totalcases))

                #sys.stdout.write("{}\n{}\n".format([c.value for c in years], [c.value for c in weeks]))
                #sys.stdout.write("{}: {}\n".format(len(row), [c.value for c in row]))
                #for i in range(2,55):
                #    sys.stdout.write("{} {} {}\n".format(years[i].value, weeks[i].value, row[i].value))
            rn += 1
        success = True
    finally:
        sys.stderr.write("Parsing {}: {}\n".format(filename, success))
        if success:
            db.commit()
        

def main(virus, filenames):
    db = opendb()
    try:
        virus_idx = get_virus_id(db, virus)
        for f in filenames:
            parse_one_file(db, virus_idx, f)
    finally:
        db.close()

def main_monthly(virus, filename):
    db = opendb()
    try:
        virus_idx = get_virus_id(db, virus)
        parse_monthly_file(db, virus_idx, filename)
    finally:
        db.close()

if __name__ == "__main__":
    virus = sys.argv[1]
    filenames = sys.argv[2:]
    main(virus, filenames)

    #main_monthly(virus, filenames[0])

    #convert_to_tab_delimited(sys.argv[1])
    #store_countries(sys.argv[1])
    #db = opendb()
    #idx = get_country_id(db, "Canada", 1)
    #print(idx)
    #idx = get_country_id(db, "UK", 99)
    #print(idx)

