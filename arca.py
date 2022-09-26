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
      <A href='?pg=map' class="w3-bar-item w3-button {}">Dynamic Map</A>
    </DIV>
""".format("w3-light-grey" if page == "home" else "",
           "w3-light-grey" if page == "guide" else "",
           "w3-light-grey" if page == "search" else "",
           "w3-light-grey" if page == "map" else ""))
    
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
  <DIV class='w3-padding w3-cell-row'>
    <DIV class='w3-col'><B>Plot options:</B>       <INPUT type='checkbox' id='f_spline' name='f_spline' class='w3-check' checked><LABEL for='f_spline'> Smooth lines</LABEL>  &nbsp;&nbsp;     <INPUT type='checkbox' id='f_log' name='f_log' class='w3-check'><LABEL for='f_log'> Use log scale</LABEL>  &nbsp;&nbsp;     <INPUT type='checkbox' id='f_sep' name='f_sep' class='w3-check'><LABEL for='f_sep'> Show by country in total</LABEL></DIV>
<!--
    <DIV class='w3-col m3'><H4>Plot options:</H4></DIV>
    <DIV class='w3-col m3'>
      <INPUT type='checkbox' name='f_spline' class='w3-check' checked><LABEL> Smooth lines</LABEL>
    </DIV>
    <DIV class='w3-col m3'>
      <INPUT type='checkbox' name='f_log' class='w3-check'><LABEL> Use log scale</LABEL>
    </DIV>
    <DIV class='w3-col m3'>
      <INPUT type='checkbox' name='f_sep' class='w3-check'><LABEL> Show by country in total</LABEL>
    </DIV>
-->
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
    smooth = 'f_spline' in fields
    uselog = 'f_log' in fields
    separate = 'f_sep' in fields
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
        C.generate_plot(divname, uselog=uselog, smooth=smooth)
        sys.stdout.write("</SCRIPT><BR><BR>")
        dividx += 1

    if len(countrydata) > 1:
        # Output results object containing totals

        allcountries = [c.country for c in countrydata]
        total.write_to_file("results/" + total.csvfile, countries=allcountries)
        total.write_to_file("results/" + total.tsvfile, delimiter='\t', countries=allcountries)
        total.write_to_excel("results/" + total.xlsfile, countries=allcountries)
        
        tblname = "table_" + str(dividx)
        divname = "plot_" + str(dividx)
        sys.stdout.write("""<DIV class='w3-bar w3-food-aubergine w3-padding'>
<DIV class="w3-bar-item"><SPAN class='w3-xlarge'>{}</SPAN></DIV>
<DIV class="w3-bar-item w3-right"><SPAN class='w3-large'><INPUT type='checkbox' id='ch1_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch1_{}'>Table</LABEL> | <INPUT type='checkbox' id='ch2_{}' onchange='toggle_visible(this.checked, "{}", {});'> <LABEL for='ch2_{}'>Plot</LABEL>""".format(total.country, dividx, tblname, dividx, dividx, dividx, divname, dividx, dividx))
        sys.stdout.write(""" | Download as: <A href='results/{}' download>Comma-delimited</A> - <A href='results/{}' download>Tab-delimited</A> - <A href='results/{}' download>Excel</A>""".format(total.csvfile, total.tsvfile, total.xlsfile))

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
        if separate:
            arcaquery.multi_country_plot(divname, countrydata, uselog, smooth)
        else:
            total.generate_plot(divname, uselog=uselog, smooth=smooth)
        sys.stdout.write("</SCRIPT><BR><BR>")
        
    sys.stdout.write("</DIV> <!-- close panel -->\n")

def generateMapMenu(name, choices, value):
    menu = """
<SELECT id='{}' name='{}' class='w3-input w3-border' onchange='validate_submit_map("{}");'>
""".format(name, name, name)
    menu += "<OPTION value='0'>Choose one...</OPTION>"
    for row in choices:
        menu += "<OPTION value='{}' {}>{}</OPTION>".format(row[0], "selected" if str(row[0]) == value else "", row[1])
    menu += "</SELECT>\n"
    return menu

def showMap(fields):
    F = arcadb.FormData()
    F.load()
    sy = int(F.start_year)
    ey = int(F.end_year)
    years = [ [x, x] for x in list(range(sy, ey+1)) ]

    # Get menu selections if present
    year = fields["f_year"].value if "f_year" in fields else "0"
    virus = fields["f_virus"].value if "f_virus" in fields else "0"
    drange = fields["f_range"].value if "f_range" in fields else "weekly"
    cumulative = (drange == "cumulative")
    
    sys.stdout.write("""<DIV class="w3-panel" id="mainpanel">
  <H1>ARCA - Dynamic Map</H1>
  <FORM action='#' id='arca_map' method='post'>
    <DIV class='w3-cell-row w3-padding'>
      <DIV class='w3-col m3 w3-padding'><LABEL>Virus:</LABEL>
""")
    sys.stdout.write(generateMapMenu('f_virus', F.viruses, virus))
    sys.stdout.write("""</DIV><DIV class='w3-col m3 w3-padding'><LABEL>Year:</LABEL>
""")
    sys.stdout.write(generateMapMenu('f_year', years, year))
    if year == "0" or virus == "0":
        status = "disabled"
    else:
        status = ""
    sys.stdout.write("""</DIV>
<DIV class='w3-col m3 w3-padding'><LABEL>Cases:</LABEL><BR>
  <INPUT class='w3-radio' type='radio' name='f_range' value='weekly' {}> Weekly <INPUT class='w3-radio' type='radio' name='f_range' value='cumulative' {}> Cumulative
</DIV>
<DIV class='w3-col m3 w3-padding'>
<LABEL>&nbsp;</LABEL><BR><INPUT id='map_submit' type='submit' class='w3-btn w3-green w3-round-large w3-large' {} value='Go!'>
</DIV>
</DIV>
</FORM>""".format("" if cumulative else "checked", "checked" if cumulative else "", status))

    if year != "0" and virus != "0":
        db = arcadb.opendb()
        try:
            data = arcadb.getCasesForMap(db, virus, year, cumulative=cumulative)
        finally:
            db.close()

        maxcases = max([ row[2] for row in data ])
        maxweek = data[0][0]

        sys.stdout.write("""  <CENTER>
      <FORM>
        <INPUT class='w3-btn w3-green w3-round-large' type='button' value='<< Previous' onclick='updateSlider(-1);'> <INPUT id='weekslider' type='range' min="1" max="{}" value="1" class="slider" style="width: 80%;"> <INPUT class='w3-btn w3-green w3-round-large' type='button' value='Next >>' onclick='updateSlider(1);'><BR>
Week <SPAN id='slidervalue'>1</SPAN>
      </FORM>
<HR>
        <DIV id='mapcontainer' class='mapcontainer'>
          <DIV class='mapdiv' id="mapdiv1"></DIV>
        </DIV>
        <BR><BR><BR><BR><BR><BR><BR><BR>
      <SCRIPT>

        var layout = {{mapbox: {{center: {{lon: -80, lat: 0}}, zoom: 2.2}},
                  title: {{'text': '{}', 'font': {{'size': 36}} }},
                  width: 800, height:1100}};

        var config = {{mapboxAccessToken: "pk.eyJ1IjoiYXJpdmE2NyIsImEiOiJjbDdrdHQ0dDQwdDB4M3ZtcTI1MXQ2cmd6In0.ZAV9aHnwaHEIxCyq6O3fVA"}};

        """.format(maxweek, "Cumulative cases" if cumulative else "Weekly cases"))

        countries = []
        cases = []
        week = maxweek
        for d in data:
            if d[0] == week:
                countries.append('"' + d[1] + '"')
                cases.append(str(d[2]))
            else:
            # Week is finished, write it out
                sys.stdout.write("""    
    var data{} = [{{
        type: "choroplethmapbox", locations: ['Vatican',{}], z: [{},{}],
      geojson: "https://salemilab.epi.ufl.edu/ARCA/map/countries-fixed.geojson"
    }}];
    """.format(week, ",".join(countries), maxcases, ",".join(cases)))

                week = d[0]
                countries = ['"' + d[1] + '"']
                cases = [str(d[2])]

        sys.stdout.write("""    
    var data{} = [{{
        type: "choroplethmapbox", locations: ['Vatican',{}], z: [{},{}],
      geojson: "https://salemilab.epi.ufl.edu/ARCA/map/countries-fixed.geojson"
    }}];
    """.format(week, ",".join(countries), maxcases, ",".join(cases)))

#        for i in range(maxweek, 0, -1):
#            sys.stdout.write("""
#        Plotly.newPlot('map{}', data{}, layout, config);
#""".format(i, i))

        sys.stdout.write("""

        var slider = document.getElementById("weekslider");
        var output = document.getElementById("slidervalue");
        function updateMap() {
            v = slider.value;
            output.innerHTML = v;
            Plotly.react('mapdiv1', eval("data" + v), layout, config);
        }
        slider.oninput = updateMap;
        function updateSlider(x) {
          slider = document.getElementById("weekslider");
          current = parseInt(slider.value);
          newvalue = current + x;
          if ((newvalue >= slider.min) && (newvalue <= slider.max)) {
            slider.value = newvalue;
            updateMap();
          }
        }
        Plotly.newPlot('mapdiv1', data1, layout, config);
      </SCRIPT>
      </CENTER>
    """)
        
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
    elif page == "map":
        showMap(fields)
    closing()

if __name__ == "__main__":
    sys.stdout.write("Content-type: text/html\n\n")
    main()
    
