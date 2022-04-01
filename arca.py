#!/usr/bin/env python

import sys
import cgi
import arcadb
import arcaquery

# Util

def loadFile(filename, data):
    with open(filename, "r") as f:
        text = f.read()
    sys.stdout.write(text.format(**data))

def getValues(fields, key):
    if key in fields:
        m = fields[key]
        if type(m).__name__ == 'list':
            return [ x.value for x in m ]
        else:
            return [ m.value ]
    else:
        return []
    
# HTML generation

def preamble(page):
    sys.stdout.write("""<!DOCTYPE html>
<HTML>
    <HEAD>
    <TITLE>ARCA - Arborvirus Reported Cases in the Americas</TITLE>
    <LINK rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <link rel="stylesheet" href="https://www.w3schools.com/lib/w3-colors-food.css">
    <LINK rel="stylesheet" href="arca.css">
    <SCRIPT src="https://cdn.plot.ly/plotly-2.9.0.min.js"></SCRIPT>
    <SCRIPT src="arca.js"></SCRIPT>
    </HEAD>
    <BODY>
    <DIV class='w3-cell-row w3-green w3-padding-16'>
      <TABLE width='100%'>
        <TR>
          <TD width='25%'>&nbsp;<IMG src='img/ARCA_Logo_crop.png' height='125px'></TD>
          <TD class='w3-center'><SPAN class="pagetitle">ARCA</SPAN><BR><SPAN class="pagesubtitle">Arbovirus Reported Cases in the Americas</SPAN></TD>
          <TD width='25%' valign='middle'><IMG align='right' src='img/UFLogo_crop.png' height='40px'>&nbsp;</TD>
        </TR>
      </TABLE>
    </DIV>
    <DIV class="w3-bar w3-food-aubergine w3-xlarge">
      <A href='?pg=home' class="w3-bar-item w3-button {}">Home</A>
      <A href='?pg=summary' class="w3-bar-item w3-button {}">ARCA Summary</A>
      <A href='?pg=search' class="w3-bar-item w3-button {}">Search ARCA</A>
    </DIV>
""".format("w3-light-grey" if page == "home" else "",
           "w3-light-grey" if page == "guide" else "",
           "w3-light-grey" if page == "search" else ""))
    
def closing():
    sys.stdout.write("""    
    <DIV class='w3-cell-row w3-green footer w3-padding'><DIV class='w3-cell'>&nbsp;&copy; 2022 Salemi Lab, University of Florida</DIV></DIV>
   </BODY>
</HTML>
""")

def showHome():
    db = arcadb.opendb()
    try:
        data = arcadb.getSummaryData(db)
        sys.stdout.write("""<DIV class="w3-panel">""")
        loadFile("txt/main.txt", data)
        sys.stdout.write("""</DIV>""")
    finally:
        db.close()
        
def showSummary():
    db = arcadb.opendb()
    try:
        data = arcadb.getSummaryData(db)
        sys.stdout.write("""<DIV class="w3-panel">""")
        loadFile("txt/stats.txt", data)
        sys.stdout.write("""</DIV>""")
    finally:
        db.close()
        
# Search page

def generateMenu(name, choices, rows=4):
    menu = """
<SELECT id='{}' name='{}' class='w3-input w3-border' multiple size='{}' onchange='validate_submit("{}");'>
""".format(name, name, rows, name)
    for row in choices:
        menu += "<OPTION value='{}'>{}</OPTION>".format(row[0], row[1])
    menu += "</SELECT>\n"
    return menu

def showSearch():
    F = arcadb.FormData()
    F.load()
    
    sys.stdout.write("""<DIV class="w3-panel">
    <H1>ARCA - Search</H1>
""")
    loadFile("txt/guide.txt", {})
    sys.stdout.write("""
    <FORM action="#" id="arca_search" method="post">
    <DIV class='w3-cell-row w3-padding'>
      <DIV class='w3-col m4 w3-padding'><LABEL>Choose one or more viruses:</LABEL>
""")
                     
    sys.stdout.write(generateMenu('f_viruses', F.viruses))
    sys.stdout.write("""    </DIV>
      <DIV class='w3-col m4 w3-padding'><LABEL>Choose start year:</LABEL>
        <INPUT name='f_start_year' type='number' value='{}' min='{}' max='{}' class='w3-input w3-border'>
        <LABEL>Choose start week:</LABEL>
        <INPUT name='f_start_week' type='number' value='1' min='1' max='53' class='w3-input w3-border'>
      </DIV>
      <DIV class='w3-col m4 w3-padding'><LABEL>Choose end year:</LABEL>
        <INPUT name='f_end_year' type='number' value='{}' min='{}' max='{}' class='w3-input w3-border'>
        <LABEL>Choose end week:</LABEL>
        <INPUT name='f_end_week' type='number' value='53' min='1' max='53' class='w3-input w3-border'>
      </DIV>
  </DIV>""".format(F.start_year, F.start_year, F.end_year, F.end_year, F.start_year, F.end_year))
    sys.stdout.write("""<DIV class='w3-cell-row w3-padding'>
  <DIV class='w3-col m6 w3-padding'><LABEL>Choose geographical region:</LABEL>
""")
    sys.stdout.write(generateMenu('f_region', F.regions, rows=12))
    sys.stdout.write("""</DIV>
  <DIV class='w3-col m6 w3-padding'><LABEL>Choose countries:</LABEL>
""")
    sys.stdout.write(generateMenu('f_country', F.countries, rows=12))
    sys.stdout.write("""</DIV>
  </DIV>
  <DIV class='w3-padding'>
    <INPUT id='search_submit' name="search_submit" type='submit' value='Submit' class='w3-btn w3-green w3-round-large w3-large' disabled><BR><span id='warn_msg'>Please select at least one virus and at least one region or country.</span><BR><BR><BR>
  </DIV>
</FORM>
</DIV>
""")

def getResults(fields):
    virus_ids = getValues(fields, "f_viruses")
    region_ids = getValues(fields, "f_region")
    country_ids = getValues(fields, "f_country")
    
    start_year = int(fields["f_start_year"].value)
    start_week = int(fields["f_start_week"].value)
    end_year = int(fields["f_end_year"].value)
    end_week = int(fields["f_end_week"].value)

    results = []
    db = arcadb.opendb()
    try:
        for countryid in country_ids:
            C = arcaquery.Results(countryid)
            C.query(db, virus_ids, start_year, start_week, end_year, end_week)
            results.append(C)
            C.write_to_file("results/" + C.csvfile)
            C.write_to_file("results/" + C.tsvfile, delimiter='\t')
            C.write_to_excel("results/" + C.xlsfile)
    finally:
        db.close()
    return results
    
def showResults(fields):
    countrydata = getResults(fields)
    sys.stdout.write("""<DIV class="w3-panel" id="mainpanel">
  <H1>ARCA - Results</H1>
""")
    dividx = 1
    total = countrydata[0].clone()
    for C in countrydata:
        total.add(C)
        tblname = "table_" + str(dividx)
        divname = "plot_" + str(dividx)

        sys.stdout.write("""<DIV class='w3-bar w3-food-aubergine w3-padding'>
<DIV class="w3-bar-item"><SPAN class='w3-xlarge'>{}</SPAN></DIV>
<DIV class="w3-bar-item w3-right"><SPAN class='w3-large'><INPUT type='checkbox' id='ch1_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch1_{}'>Table</LABEL> | <INPUT type='checkbox' id='ch2_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch2_{}'>Plot</LABEL>""".format(C.country, dividx, tblname, dividx, dividx, dividx, divname, dividx, dividx))
        sys.stdout.write(""" | Download as: <A href='results/{}' download>Comma-delimited</A> - <A href='results/{}' download>Tab-delimited</A> - <A href='results/{}' download>Excel</A>""".format(C.csvfile, C.tsvfile, C.xlsfile))

        sys.stdout.write("""</SPAN></DIV></DIV>""")
        
        sys.stdout.write("""<DIV id='{}' style='display:none;'><TABLE class='w3-table w3-striped w3-border'>
<TR>
{}
</TR>
        """.format(tblname, C.headers))

        for k in sorted(C.data.keys()):
            row = C.data[k]
            sys.stdout.write(C.rowformat.format(*row))
        sys.stdout.write("""</TABLE></DIV>
<DIV id='{}' style='display:none;' class='plotdiv'></DIV>
<SCRIPT>""".format(divname))
        C.generate_plot(divname)
        sys.stdout.write("</SCRIPT><BR><BR>")
        dividx += 1

    tblname = "table_" + str(dividx)
    divname = "plot_" + str(dividx)
    sys.stdout.write("""<DIV class='w3-bar w3-food-aubergine w3-padding'>
<DIV class="w3-bar-item"><SPAN class='w3-xlarge'>{}</SPAN></DIV>
<DIV class="w3-bar-item w3-right"><SPAN class='w3-large'><INPUT type='checkbox' id='ch1_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch1_{}'>Table</LABEL> | <INPUT type='checkbox' id='ch2_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch2_{}'>Plot</LABEL>""".format(total.country, dividx, tblname, dividx, dividx, dividx, divname, dividx, dividx))
#    sys.stdout.write(""" | Download as: <A href='results/{}' download>Comma-delimited</A> - <A href='results/{}' download>Tab-delimited</A> - <A href='results/{}' download>Excel</A>""".format(C.csvfile, C.tsvfile, C.xlsfile))

    sys.stdout.write("""</SPAN></DIV></DIV>""")
        
    sys.stdout.write("""<DIV id='{}' style='display:none;'><TABLE class='w3-table w3-striped w3-border'>
<TR>
{}
</TR>
        """.format(tblname, total.headers))

    for k in sorted(total.data.keys()):
        row = total.data[k]
        sys.stdout.write(total.rowformat.format(*row))
    sys.stdout.write("""</TABLE></DIV>
<DIV id='{}' style='display:none;' class='plotdiv'></DIV>
<SCRIPT>""".format(divname))
    total.generate_plot(divname)
    sys.stdout.write("</SCRIPT><BR><BR>")
        
    sys.stdout.write("</DIV> <!-- close panel -->\n")
    
def main():
    fields = cgi.FieldStorage()
    if "search_submit" in fields:
        page = "results"
    elif "pg" in fields:
        page = fields["pg"].value
    else:
        page = "home"
    preamble(page)

    if page == "home":
        showHome()
    elif page == "summary":
        showSummary()
    elif page == "search":
        showSearch()
    elif page == "results":
        showResults(fields)
        
    closing()

if __name__ == "__main__":
    sys.stdout.write("Content-type: text/html\n\n")
    main()
    
